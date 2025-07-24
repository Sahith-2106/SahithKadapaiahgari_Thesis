import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

def create_tei_xml(json_folder, output_file):
    """Create a TEI XML document from multiple JSON files."""
    
    # Create TEI root with namespace
    tei = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    
    # Create teiHeader with basic metadata
    teiHeader = ET.SubElement(tei, "teiHeader")
    fileDesc = ET.SubElement(teiHeader, "fileDesc")
    
    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    ET.SubElement(titleStmt, "title").text = "Generated TEI Document"
    ET.SubElement(titleStmt, "author").text = "Automated Conversion"
    
    publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
    ET.SubElement(publicationStmt, "publisher").text = "TEI Conversion Tool"
    ET.SubElement(publicationStmt, "date", when=datetime.now().isoformat())
    
    sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
    ET.SubElement(sourceDesc, "p").text = "Converted from JSON OCR results"
    
    # Create text structure
    text = ET.SubElement(tei, "text")
    front = ET.SubElement(text, "front")
    body = ET.SubElement(text, "body")
    back = ET.SubElement(text, "back")
    
    # Get and sort JSON files
    json_files = sorted(
        [f for f in os.listdir(json_folder) if f.endswith('.json') and not f.startswith('.')],
        key=lambda x: (
            0 if 'front' in x.lower() else 
            2 if 'back' in x.lower() else 
            1, x
        )
    )
    
    # TEI element mapping for common labels
    TEI_ELEMENT_MAP = {
        'heading': 'head',
        'title': 'head',
        'text': 'p',
        'footnote': 'note',
        'quote': 'quote',
        'list': 'list',
        'list_item': 'item',
        'figure': 'figure',
        'table': 'table',
        'image': 'graphic'
    }
    
    # Process each JSON file
    for json_file in json_files:
        file_path = os.path.join(json_folder, json_file)
        base_name = os.path.splitext(json_file)[0].replace('_ocr', '')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine which section this belongs to
        if 'front' in base_name.lower():
            parent = front
            div_type = "frontmatter"
        elif 'back' in base_name.lower():
            parent = back
            div_type = "backmatter"
        else:
            parent = body
            div_type = f"page-{base_name}"
        
        # Create division for this section
        div = ET.SubElement(parent, "div", type=div_type)
        
        # Process each section in the JSON
        for section in data.get('sections', []):
            label = section.get('label', '')
            text_content = section.get('ocr_text', '').strip()
            
                
            # Handle special cases first
            if label == 'pagenumber':
                ET.SubElement(div, "pb", n=text_content)
                continue
            
            # Get appropriate element name
            element_name = TEI_ELEMENT_MAP.get(label, label)
            
            try:
                # Try to create the element
                if element_name in ['note', 'item']:
                    elem = ET.SubElement(div, element_name, type=label)
                else:
                    elem = ET.SubElement(div, element_name)
                
                elem.text = text_content
            
                    
            except Exception:
                # Fallback for invalid XML tag names
                elem = ET.SubElement(div, "item", type=label)
                elem.text = text_content
    
    # Generate pretty-printed XML
    xml_str = ET.tostring(tei, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    # Remove extra XML declaration added by minidom
    pretty_xml = '\n'.join(pretty_xml.split('\n')[1:])
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(pretty_xml)
    
    print(f"Successfully created TEI XML at {output_file}")

if __name__ == "__main__":
    # Configuration - update these paths
    JSON_FOLDER = "Path to input folder"
    OUTPUT_FILE = "Path to save xml file"
    
    create_tei_xml(JSON_FOLDER, OUTPUT_FILE)