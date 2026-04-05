# File Upload Milestone

## Current State
The document module has been upgraded from metadata-only document records toward actual file upload support.

## Intended Capabilities
- File picker on Upload Document page
- Accept file types such as PDF, DOCX, DOC, TXT, JPG, JPEG, PNG
- Save uploaded files into a local uploads folder
- Store document metadata and file path in SQLite
- Display document records under Trust Detail and Property Detail

## Current Product Position
The app now includes:
- Trust persistence
- Property persistence
- Account persistence
- Improved trust dropdown labels
- In-progress real file upload capability

## Next Recommended Checks
1. Verify file chooser appears on upload page
2. Verify uploaded file is saved into uploads/
3. Verify document metadata is saved into SQLite
4. Verify trust/property detail pages reflect uploaded documents after restart
5. Continue with ledger persistence after file upload is confirmed stable