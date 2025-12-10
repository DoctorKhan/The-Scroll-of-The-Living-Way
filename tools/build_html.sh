#!/bin/bash
set -e

# Configuration
TEMPLATE="templates/guide_template.html"
ORNAMENT_MARKER="ORNAMENT-MARKER-XYZ"
# We use a pipe | as delimiter in perl, so no need to escape / in </div>
ORNAMENT_HTML='<div class="ornament">✦ ✦ ✦</div>'

echo "--- Starting HTML Build ---"

# Function to process TeX files
process_tex() {
    local tex_file="$1"
    local base_name=$(basename "$tex_file" .tex)
    local html_file="${base_name}.html"
    local temp_tex="${base_name}.temp.tex"
    
    # Skip if it's a temp file
    if [[ "$tex_file" == *".temp.tex" ]]; then return; fi

    echo "Converting $tex_file..."
    
	    # 1. Pre-process LaTeX for Pandoc
	    #    a. Replace bare \ornament lines with a unique marker that we can
	    #       turn into a decorative divider in HTML.
	    #    b. Treat verse "stanza breaks" (blank line after a line ending in \\)
	    #       as real paragraph breaks by removing the trailing \\ in that
	    #       position. This lets Pandoc emit separate <p> blocks, so stanza
	    #       gaps appear in HTML the same way they do in the PDF.
	    perl -0pe 's/^\s*\\ornament\s*$/'"$ORNAMENT_MARKER"'/mg' "$tex_file" | \
	    perl -0pe 's/\\+\s*\n\s*\n/\n\n/g' > "$temp_tex"
    
    # Derive title from filename (replace underscores with spaces)
    local title="${base_name//_/ }"
    
    # 2. Run Pandoc
    pandoc "$temp_tex" \
        -o "$html_file" \
        --template="$TEMPLATE" \
        --to=html \
        --metadata title="$title" \
        --standalone

    # 3. Post-process: Replace the marker with the actual HTML ornament
    # Using perl for robust in-place replacement with different delimiter
    perl -i -pe "s|$ORNAMENT_MARKER|$ORNAMENT_HTML|g" "$html_file"
    
    # Cleanup invalid HTML (div inside p) produced by pandoc wrapping the marker
    perl -i -pe 's|<p>\s*(<div class="ornament">.*?</div>)\s*</p>|$1|g' "$html_file"
    
    # Cleanup
    rm "$temp_tex"
    echo "✓ Generated $html_file"
}

# Process all .tex files in the root directory
for f in *.tex; do
	# Skip temporary/debug TeX files
	if [[ "$f" == debug_* ]]; then
		continue
	fi
	# Check if file exists to avoid errors if no matches
	[ -e "$f" ] || continue
	process_tex "$f"
done

# Process the Guide (Markdown)
if [ -f "living-way-guide.md" ]; then
    echo "Converting living-way-guide.md..."
    pandoc living-way-guide.md \
        -o living_way_guide.html \
        --template="$TEMPLATE" \
        --metadata title="A Guide to The Way of the Living Jesus" \
        --standalone
    echo "✓ Generated living_way_guide.html"
fi

echo "--- HTML Build Complete ---"
