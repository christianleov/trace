# Backend

## Backend hosted on the Supabase platform
The backend is deployed by [Supabase](https://supabase.com/) for convenient user authentication, security, and database (postgres) access.

## API communication between frontend (fe) and backend (be)
We use a REST API implemented with [FastAPI](https://fastapi.tiangolo.com/) for communication between the frontend and backend.

The backend receives an image from the frontend to process.
The billing information of that images is extracted and stored in a database.
Afterward, the frontend can query the backend to receive information from the database.

## Processing of images (image to database entry)
A couple of steps are required to convert an image to a database entry:

* [image_process.py](image_process.py): Image processing (contrast enhancement, straightening, ...)
* [ocr.py](ocr.py): Optical Character Recognition (OCR) converts the processed image to text
* [text_process.py](text_process.py): Text processing converts the text to a database entry
