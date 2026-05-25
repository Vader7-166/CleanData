## 1. Quick Lookup Tool on HSTaxonomy Page

- [x] 1.1 Add state variables (`lookupHsCode`, `lookupResult`, `lookupLoading`, `lookupError`) for the quick lookup functionality in `HSTaxonomy.tsx`.
- [x] 1.2 Implement the UI layout for the Card "Tra cứu nhanh mã HS" at the top of the `HSTaxonomy` page, featuring an input and a "Tra cứu" button.
- [x] 1.3 Implement the API handler call to `/api/taxonomy/check-hs-codes` and display the results or errors inside a card with badges and clean labels.

## 2. Dialog Form Enhancements

- [x] 2.1 Replace the fixed dropdown `Select` for `formDongSp` (Product Line) with a free-text `Input` field in the Dialog markup.
- [x] 2.2 Add an "Auto Lookup / Tra cứu tự động" button next to the "Mã HS" input in the Add/Edit Dialog.
- [x] 2.3 Implement the handler for the auto lookup button to call the check-hs-codes endpoint and set state for `formDongSp`, `formIndustryName`, and `formDefaultType` dynamically.

## 3. Verification

- [x] 3.1 Verify both the Quick Lookup card and the Dialog autofill feature work correctly in the browser.
