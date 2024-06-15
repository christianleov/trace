import argparse
import email
import email.message
import email.policy
import hashlib
import pathlib
import subprocess
import sys

DATA_DIR = (pathlib.Path(__file__).parent / "data").resolve()
EBON_DIR = DATA_DIR / "ebons"


def call_getmail() -> None:
    cmd = "getmail"
    subprocess.call(cmd)


def __read_mail_file(path: pathlib.Path) -> email.message.Message:
    with open(path, "r") as file:
        email_content = file.read()
    message = email.message_from_string(
        email_content,
        policy=email.policy.default,
    )
    return message


def __extract_pdf_attachment(message) -> (str, bytes):
    for part in message.walk():
        content_disposition = str(part.get("Content-Disposition"))

        if "attachment" in content_disposition:
            # This is an attachment
            filename = part.get_filename()
            attachment_data = part.get_payload(decode=True)
            return filename, attachment_data
    raise ValueError("No attachment found.")


def extract_attachments(mail_dir: pathlib.Path) -> None:
    skipped = 0
    for file_path in (mail_dir / "new").glob("*.L"):
        message = __read_mail_file(file_path)
        try:
            name, attachment = __extract_pdf_attachment(message)
        except ValueError:
            continue
        if name != "REWE-eBon.pdf":
            print(f"Skipping attachment with name {name}")
            continue
        hash_ = hashlib.sha256(attachment).hexdigest()
        ebon_file_path = EBON_DIR / f"REWE-eBon-{hash_}.pdf"
        if ebon_file_path.exists():
            skipped += 1
            continue
        with open(ebon_file_path, "wb") as f:
            f.write(attachment)
            print(f"Attachment written to {ebon_file_path}")
    print(f"Skipped {skipped} eBons (already parsed)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Read mails and extract attachments")
    parser.add_argument(
        "mail_dir",
        type=pathlib.Path,
        help="Directory to mail folder from getmail",
    )
    args = parser.parse_args()
    if not (args.mail_dir / "new").exists():
        print(f"{args.mail_dir} seems to be an incorrect mail directory")
        sys.exit(-1)
    return args


def main():
    args = parse_args()
    call_getmail()
    extract_attachments(args.mail_dir)


if __name__ == "__main__":
    main()
