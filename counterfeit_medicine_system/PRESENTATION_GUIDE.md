# Counterfeit Medicine System: Presentation Guide

## Before your presentation

1. Extract the project folder to a normal writable folder, such as `C:\Sparsh\Counterfeit_Medicine_System`.
2. Open the folder in VS Code.
3. Double-click `run_windows.bat`, or run the commands in `README.md` from the VS Code terminal.
4. Open http://localhost:8000 in the browser (or your Vercel URL).
5. On the Medicine database page, sync 500 reference listings before presentation if the internet works. Keep `data\medicine_reference.db` in the project folder. The saved database then works offline for browsing and checking those downloaded listings.
6. If the API is unavailable, use the clearly fictional presentation example. Do not describe the 12 demo rows as real medicines.

## Suggested five-minute walkthrough

### 1. Problem and objective, 30 seconds

“Counterfeit medicines are a public-safety concern. My project is a student prototype to help a user review medicine label details against a reference catalogue and flag inconsistent dates or product details.”

### 2. Show the overview, 30 seconds

Point out the dashboard, navigation, catalogue status, and the safety note. Explain that the interface is a Tailwind CSS web page served with FastAPI and uses SQLite for local storage.

### 3. Demonstrate a label check, 90 seconds

1. Open **Verify medicine**.
2. Click **Load sample presentation case**.
3. Explain that every sample field is fictional and used only to show the workflow.
4. Click **Review medicine details**.
5. Show the result and explain why a demo match does not mean a medicine is genuine.
6. Change the manufacturing date to a future date or set the expiry before manufacturing. Submit again to demonstrate the date-warning logic.

### 4. Show the database, 60 seconds

1. Open **Medicine database**.
2. Explain the difference between demo rows and openFDA reference listings.
3. Show search, source filters, the table and CSV export.
4. If online, use **Sync 500 records** and point to the official-record count. Do not make an API request live if the venue's internet is unreliable. Sync beforehand.

### 5. Architecture and limitations, 60 seconds

Explain the flow:

Label inputs → validation and date checks → SQLite product-reference search → result message → manual follow-up with a pharmacist or manufacturer.

State the main limitation clearly: “This version does not connect to a manufacturer's batch-authentication service. A product listing match cannot prove that a physical pack is genuine. The openFDA listing data is US-focused and is not an Indian drug-approval database.”

### 6. Future work, 30 seconds

- Integrate an authorized Indian product-data source.
- Connect a manufacturer-approved batch or serial-number verification API.
- Add barcode or QR scanning with server-side validation.
- Test with pharmacists and validated sample cases.

## Likely viva questions

**Q: Does the system confirm whether a medicine is genuine?**

A: No. This prototype checks product-reference listings, entered manufacturer text, product codes and date consistency. Genuine batch authentication needs an authorized manufacturer or regulator service.

**Q: Where does the catalogue come from?**

A: The sync feature requests product listings from the openFDA National Drug Code Directory API. The data is labeler-submitted and US-focused. The app records the source and sync time.

**Q: Why do you need a batch number if the source cannot verify it?**

A: The app records it in the local screening report and explains the limitation. The batch number is not checked against an authorized batch system in this prototype.

**Q: What if the database has no match?**

A: A missing match is inconclusive. The item might be from another country, use a different spelling, or be missing from the reference catalogue. It is not proof of counterfeiting.

**Q: What is the technology stack?**

A: Python provides the application logic, FastAPI provides the API, a Tailwind CSS page provides the interface, and SQLite stores reference records.

**Q: What is required for real deployment in India?**

A: A reliable India-specific source and an authorized batch-verification integration, plus data-quality checks, privacy safeguards and independent validation.

## Do not claim during the presentation

- Do not claim the app independently certifies medicine authenticity.
- Do not call the openFDA listings “500 verified genuine medicines.” Call them “500 product-reference listings.”
- Do not imply automatic integration with CDSCO. The project only links to public CDSCO resources.
- Do not use a real medicine decision based solely on this prototype.
