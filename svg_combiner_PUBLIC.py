"""
SVG Multi-Page Combiner for Inkscape
=====================================

Recursively combines SVG files from nested directory structures into a single
multi-page Inkscape document. Perfect for organizing design files with multiple
layers that need to be consolidated for production workflows.

USE CASE:
You have a directory structure like this:
    Root/
    ├── Design_A/
    │   ├── layer1/file.svg
    │   └── layer2/file.svg
    ├── Design_B/
    │   ├── file1.svg
    │   └── file2.svg
    └── ...

And you want ONE Inkscape file with:
- Each design on its own page
- All layers for that design stacked and centered
- Proper layer naming for easy organization

FEATURES:
- Handles mixed directory structures (nested folders or flat)
- Natural sorting (name_1, name 1, name-1, name01 all work)
- Automatic centering of all content
- Dynamic output naming based on root folder
- Preserves original SVG content and styling

REQUIREMENTS:
- Python 3.x
- lxml library: pip install lxml

USAGE:
1. Run the script: python svg_combiner.py
2. Enter the root folder path when prompted
3. Confirm the operation
4. Open the output file in Inkscape

Created by: Emily (fabricator/maker) with assistance from Claude (AI)
Shared for the maker/artisan community because we all deserve better workflows.

License: MIT (use it, modify it, share it, just don't blame us if it breaks)
Repository: [Your gist URL here]
Version: 1.0
Date: December 2024
"""

import os
import sys
from pathlib import Path
from lxml import etree
import re

# ============================================================================
# CONFIGURATION SECTION - Change these settings as needed
# ============================================================================

# Output filename options:
# - Set to None to use root folder name + "_ALL.svg"
# - Set to "ASK" to prompt user for filename  
# - Set to specific name like "My_Design.svg" to use that
OUTPUT_FILENAME = None  # Default: uses folder name + "_ALL.svg"

# Page dimensions in inches
PAGE_WIDTH = 12
PAGE_HEIGHT = 12

# DPI for converting inches to pixels (Inkscape default is 96)
# Common values: 72 (older standard), 96 (current standard), 300 (print quality)
DPI = 96

# Calculate page dimensions in pixels (used internally)
PAGE_WIDTH_PX = PAGE_WIDTH * DPI
PAGE_HEIGHT_PX = PAGE_HEIGHT * DPI

# SVG namespaces - required for proper XML handling
# These tell the XML parser how to interpret Inkscape-specific elements
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"

# Register namespaces so lxml generates proper prefixes
etree.register_namespace('svg', SVG_NS)
etree.register_namespace('inkscape', INKSCAPE_NS)
etree.register_namespace('sodipodi', SODIPODI_NS)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def natural_sort_key(text):
    """
    Sort strings containing numbers naturally (1, 2, 10 instead of 1, 10, 2).
    
    Handles various naming conventions:
    - name_1, name_2, name_10
    - name 1, name 2, name 10
    - name-1, name-2, name-10
    - name01, name02, name10
    
    Args:
        text: String or Path object to generate sort key for
        
    Returns:
        List of strings and integers for natural sorting
    """
    def atoi(text):
        return int(text) if text.isdigit() else text.lower()
    
    return [atoi(c) for c in re.split(r'(\d+)', str(text))]


def find_all_svgs(root_path):
    """
    Recursively find all SVG files in the directory structure.
    Groups them by their immediate parent folder.
    
    This function walks through the entire directory tree starting from root_path,
    finds every .svg file, and organizes them by which parent folder they're in.
    It handles both nested directories (where each layer is in its own folder) and
    flat directories (where all SVGs are in one folder).
    
    Args:
        root_path: Path object pointing to the root directory to scan
        
    Returns:
        Dictionary where:
        - Keys are parent folder names (strings)
        - Values are lists of Path objects pointing to SVG files
        
    Example return:
        {
            'Design_A': [Path('Design_A/layer1.svg'), Path('Design_A/layer2.svg')],
            'Design_B': [Path('Design_B/file1.svg'), Path('Design_B/file2.svg')]
        }
    """
    svg_groups = {}
    root_path = Path(root_path)
    
    # Iterate through each immediate subdirectory
    for parent_dir in root_path.iterdir():
        if not parent_dir.is_dir():
            continue
            
        parent_name = parent_dir.name
        svg_files = []
        
        # Recursively find all SVG files under this parent
        # rglob("*.svg") finds files recursively, regardless of nesting depth
        for svg_file in parent_dir.rglob("*.svg"):
            svg_files.append(svg_file)
        
        # Sort files naturally by filename (handles numbers correctly)
        svg_files.sort(key=lambda x: natural_sort_key(x.name))
        
        # Only add to results if we found SVG files
        if svg_files:
            svg_groups[parent_name] = svg_files
            print(f"Found {len(svg_files)} SVG files in '{parent_name}'")
    
    return svg_groups


def get_svg_viewbox(svg_path):
    """
    Extract dimensions from an SVG file's viewBox or width/height attributes.
    
    SVG files can specify their dimensions in multiple ways:
    1. viewBox attribute (most reliable): "0 0 width height"
    2. width and height attributes: can have units like "100px" or "10in"
    3. Neither (rare): we fall back to page dimensions
    
    Args:
        svg_path: Path object pointing to the SVG file
        
    Returns:
        Tuple of (width, height) in pixels
        Falls back to PAGE_WIDTH_PX, PAGE_HEIGHT_PX if dimensions can't be determined
    """
    try:
        tree = etree.parse(str(svg_path))
        root = tree.getroot()
        
        # Try to get viewBox first (most reliable method)
        viewbox = root.get('viewBox')
        if viewbox:
            parts = viewbox.split()
            if len(parts) == 4:
                # viewBox format: "min-x min-y width height"
                # We only care about width and height (indices 2 and 3)
                return float(parts[2]), float(parts[3])
        
        # Fall back to width/height attributes
        width = root.get('width')
        height = root.get('height')
        
        if width and height:
            # Remove any units (px, in, cm, etc.) and convert to float
            # This regex keeps only digits and decimal points
            width = float(re.sub(r'[^0-9.]', '', width))
            height = float(re.sub(r'[^0-9.]', '', height))
            return width, height
        
        # If we couldn't find dimensions, use page size as default
        return PAGE_WIDTH_PX, PAGE_HEIGHT_PX
        
    except Exception as e:
        print(f"Warning: Could not read dimensions from {svg_path.name}: {e}")
        return PAGE_WIDTH_PX, PAGE_HEIGHT_PX


def create_centered_layer(svg_path, layer_name, page_num):
    """
    Load an SVG file and create a centered layer group for it.
    
    This function:
    1. Parses the source SVG file
    2. Extracts all the visual content
    3. Wraps it in an Inkscape layer group
    4. Calculates centering transform
    5. Names the layer appropriately
    
    Args:
        svg_path: Path object to the source SVG file
        layer_name: What to name this layer in the output
        page_num: Which page this layer belongs to (for unique IDs)
        
    Returns:
        lxml Element representing the layer group, or None if error occurred
    """
    try:
        # Parse the source SVG file
        tree = etree.parse(str(svg_path))
        root = tree.getroot()
        
        # Get the SVG's original dimensions
        svg_width, svg_height = get_svg_viewbox(svg_path)
        
        # Calculate offset to center this SVG on the page
        # If SVG is smaller than page, this centers it
        # If SVG is larger, it'll be positioned to align the centers
        offset_x = (PAGE_WIDTH_PX - svg_width) / 2
        offset_y = (PAGE_HEIGHT_PX - svg_height) / 2
        
        # Create a group element that will act as an Inkscape layer
        # The inkscape:groupmode="layer" attribute is what makes it show up
        # as a layer in Inkscape's Layers panel
        layer = etree.Element(
            f"{{{SVG_NS}}}g",  # SVG group element
            attrib={
                f"{{{INKSCAPE_NS}}}groupmode": "layer",  # Makes it a layer
                f"{{{INKSCAPE_NS}}}label": layer_name,   # Name shown in UI
                "id": f"layer_{page_num}_{layer_name.replace(' ', '_')}",  # Unique ID
                "transform": f"translate({offset_x}, {offset_y})"  # Centering
            }
        )
        
        # Copy all child elements from the source SVG into this layer
        # We skip metadata and namedview elements as they're not visual content
        for child in root:
            # Skip non-visual elements
            if child.tag.endswith(('metadata', 'namedview')):
                continue
            layer.append(child)
        
        return layer
        
    except Exception as e:
        print(f"Error processing {svg_path.name}: {e}")
        return None


def create_multipage_svg(svg_groups, output_path):
    """
    Create a multi-page Inkscape SVG document.
    
    This is the main assembly function that creates the final document structure.
    It builds a proper Inkscape multi-page document with:
    - Individual page elements for each design
    - Proper layer hierarchy within each page
    - All content centered and organized
    
    Inkscape's multi-page format (introduced in v1.2) uses:
    - <inkscape:page> elements to define page boundaries
    - Pages stacked vertically in the document
    - Groups with inkscape:groupmode="layer" for layers
    
    Args:
        svg_groups: Dictionary of {parent_name: [svg_files]} from find_all_svgs()
        output_path: Path object where the final SVG should be saved
    """
    # Create the root SVG element
    # Namespaces are declared via nsmap parameter, not as regular attributes
    root = etree.Element(
        f"{{{SVG_NS}}}svg",
        attrib={
            "width": f"{PAGE_WIDTH}in",
            "height": f"{PAGE_HEIGHT}in",
            "viewBox": f"0 0 {PAGE_WIDTH_PX} {PAGE_HEIGHT_PX}",
            "version": "1.1",
        },
        nsmap={
            None: SVG_NS,              # Default namespace (no prefix)
            'inkscape': INKSCAPE_NS,   # inkscape: prefix
            'sodipodi': SODIPODI_NS,   # sodipodi: prefix
        }
    )
    
    # Add defs section (required for proper Inkscape structure)
    # This is where styles, gradients, patterns, etc. would go
    defs = etree.SubElement(root, f"{{{SVG_NS}}}defs")
    
    # Add Inkscape-specific namedview element
    # This stores view settings, grid settings, and page definitions
    namedview = etree.SubElement(
        root,
        f"{{{SODIPODI_NS}}}namedview",
        attrib={
            "pagecolor": "#ffffff",      # White page background
            "bordercolor": "#666666",    # Gray page border
            "borderopacity": "1.0",      # Solid border
            f"{{{INKSCAPE_NS}}}document-units": "in",  # Use inches
            f"{{{INKSCAPE_NS}}}current-layer": "page_1",  # Default to first page
            "showgrid": "false",         # Don't show grid by default
        }
    )
    
    # Sort parent folders alphabetically for consistent ordering
    sorted_parents = sorted(svg_groups.keys(), key=natural_sort_key)
    
    page_num = 1
    
    # Process each parent folder as a separate page
    for parent_name in sorted_parents:
        svg_files = svg_groups[parent_name]
        
        print(f"\nProcessing page {page_num}: {parent_name}")
        print(f"  Adding {len(svg_files)} layers...")
        
        # Calculate Y offset for this page
        # Pages are stacked vertically with 100px gap between them
        page_y_offset = (page_num - 1) * (PAGE_HEIGHT_PX + 100)
        
        # Create an Inkscape page element
        # This defines the page boundary that shows in Inkscape's page selector
        page_element = etree.SubElement(
            namedview,
            f"{{{INKSCAPE_NS}}}page",
            attrib={
                "x": "0",
                "y": str(page_y_offset),
                "width": str(PAGE_WIDTH_PX),
                "height": str(PAGE_HEIGHT_PX),
                "id": f"page_{page_num}",
                f"{{{INKSCAPE_NS}}}label": f"{parent_name}",
            }
        )
        
        # Create a group to hold all layers for this page
        # This group is positioned at the page's Y offset
        page_group = etree.SubElement(
            root,
            f"{{{SVG_NS}}}g",
            attrib={
                f"{{{INKSCAPE_NS}}}groupmode": "layer",
                f"{{{INKSCAPE_NS}}}label": f"Page {page_num}: {parent_name}",
                "id": f"page_group_{page_num}",
                "transform": f"translate(0, {page_y_offset})",
            }
        )
        
        # Add each SVG file as a layer within this page group
        for idx, svg_file in enumerate(svg_files, 1):
            layer_name = f"{svg_file.stem}"  # Filename without extension
            print(f"    - {layer_name}")
            
            # Create the layer with centered content
            layer = create_centered_layer(svg_file, layer_name, page_num)
            if layer is not None:
                # Recalculate transform to be relative to page group
                svg_width, svg_height = get_svg_viewbox(svg_file)
                offset_x = (PAGE_WIDTH_PX - svg_width) / 2
                offset_y = (PAGE_HEIGHT_PX - svg_height) / 2
                
                layer.set("transform", f"translate({offset_x}, {offset_y})")
                page_group.append(layer)
        
        page_num += 1
    
    # Update the root SVG height to accommodate all pages
    # This makes the document canvas tall enough to show all pages
    total_height = (page_num - 1) * (PAGE_HEIGHT_PX + 100)
    root.set("height", f"{total_height / DPI}in")
    root.set("viewBox", f"0 0 {PAGE_WIDTH_PX} {total_height}")
    
    # Write the combined SVG to disk
    tree = etree.ElementTree(root)
    tree.write(
        str(output_path),
        pretty_print=True,      # Makes the XML human-readable
        xml_declaration=True,   # Adds <?xml version="1.0"?> header
        encoding='UTF-8'        # Standard UTF-8 encoding
    )
    
    print(f"\n✓ Successfully created {output_path}")
    print(f"  Total pages: {page_num - 1}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function - handles user input and orchestrates the combination process.
    
    This is the entry point that:
    1. Gets the root directory from user
    2. Scans for SVG files
    3. Confirms the operation
    4. Creates the combined document
    5. Reports results
    """
    print("=" * 70)
    print("SVG Multi-Page Combiner for Inkscape")
    print("=" * 70)
    print()
    
    # Get the root directory from user
    # Can be provided as command line argument or via prompt
    if len(sys.argv) > 1:
        # If a path was provided as command line argument
        root_dir = sys.argv[1]
    else:
        # Ask the user for the path
        root_dir = input("Enter the root folder path containing your SVG files:\n> ").strip()
        
        # Remove quotes if user copied path from Windows Explorer or terminal
        root_dir = root_dir.strip('"').strip("'")
    
    root_path = Path(root_dir)
    
    # Validate the path exists
    if not root_path.exists():
        print(f"\n✗ Error: Path does not exist: {root_path}")
        input("\nPress Enter to exit...")
        return
    
    # Validate it's actually a directory
    if not root_path.is_dir():
        print(f"\n✗ Error: Path is not a directory: {root_path}")
        input("\nPress Enter to exit...")
        return
    
    print(f"\nScanning directory: {root_path}")
    print("=" * 70)
    
    # Find all SVG files grouped by parent folder
    svg_groups = find_all_svgs(root_path)
    
    # Check if we found anything
    if not svg_groups:
        print("\n✗ No SVG files found in any subdirectories!")
        input("\nPress Enter to exit...")
        return
    
    # Report what we found
    print(f"\nFound {len(svg_groups)} parent folders with SVG files")
    total_svgs = sum(len(files) for files in svg_groups.values())
    print(f"Total SVG files to process: {total_svgs}")
    
    # Determine output filename based on configuration
    if OUTPUT_FILENAME == "ASK":
        # Prompt user for custom filename
        print("\n" + "=" * 70)
        filename = input("Enter output filename (without path): ").strip()
        if not filename.endswith('.svg'):
            filename += '.svg'
    elif OUTPUT_FILENAME is None:
        # Use root folder name + "_ALL.svg"
        folder_name = root_path.name
        filename = f"{folder_name}_ALL.svg"
        print(f"\nOutput filename: {filename}")
    else:
        # Use the configured filename
        filename = OUTPUT_FILENAME
    
    # Confirm before processing
    print("\n" + "=" * 70)
    response = input(f"\nCreate '{filename}' with {len(svg_groups)} pages? (y/n): ").strip().lower()
    
    if response != 'y':
        print("\nOperation cancelled.")
        input("\nPress Enter to exit...")
        return
    
    # Create the output file
    output_path = root_path / filename
    
    print("\n" + "=" * 70)
    print("Processing files...")
    print("=" * 70)
    
    try:
        # Do the actual work
        create_multipage_svg(svg_groups, output_path)
        
        # Success!
        print("\n" + "=" * 70)
        print("✓ DONE!")
        print("=" * 70)
        print(f"\nYour combined SVG file is ready:")
        print(f"  {output_path}")
        print(f"\nOpen it in Inkscape to see all {len(svg_groups)} pages.")
        print("\nEach page contains all layers from one design folder,")
        print("centered and ready for your cutting/laser software.")
        
    except Exception as e:
        # Something went wrong
        print(f"\n✗ Error creating SVG file: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")


# Standard Python idiom: only run main() if script is executed directly
# (not if it's imported as a module)
if __name__ == "__main__":
    main()
