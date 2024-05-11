import os
import sys

import fitz  # PyMuPDF

def convert_pdf_to_grayscale(input_pdf_path, output_pdf_path, out_png_dir):
    # Open the provided PDF file
    document = fitz.open(input_pdf_path)

    # Create a new PDF for output
    new_document = fitz.open()

    for page_number in range(document.page_count):
        # Get a page
        page = document.load_page(page_number)
        
        # Convert the page to a pixmap (an image)
        pixmap = page.get_pixmap()

        # Convert the pixmap to grayscale
        gray_pixmap = fitz.Pixmap(fitz.csGRAY, pixmap)

        # Save the grayscale image as a PNG file
        png_file_path = out_png
        gray_pixmap.save(png_file_path)
        print(f"Saved grayscale PNG: {png_file_path}")
        
        # Create a new PDF page with the same size as the original
        new_page = new_document.new_page(width = gray_pixmap.width, height = gray_pixmap.height)
        
        # Insert the grayscale image
        new_page.insert_image(new_page.rect, pixmap=gray_pixmap)

    # Save the new document
    new_document.save(output_pdf_path)
    new_document.close()
    document.close()
    print(f"Converted PDF saved as '{output_pdf_path}'")

# Example usage
if __name__ == "__main__":
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    out_png = sys.argv[3]
    convert_pdf_to_grayscale(input_pdf, output_pdf, out_png)
