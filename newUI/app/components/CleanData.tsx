import { Upload, FileSpreadsheet } from "lucide-react";
import { useState } from "react";

export function CleanData() {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      console.log("File uploaded:", e.dataTransfer.files[0].name);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="mb-2">Clean Data</h2>
        <p className="text-muted-foreground">
          Tải lên tệp Excel để làm sạch dữ liệu
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Upload className="w-8 h-8 text-primary" />
            </div>
            <div>
              <p className="mb-2">
                Kéo thả tệp Excel vào đây hoặc{" "}
                <label className="text-primary cursor-pointer hover:underline">
                  chọn tệp
                  <input type="file" accept=".xlsx,.xls,.csv" className="hidden" />
                </label>
              </p>
              <p className="text-muted-foreground">
                Hỗ trợ định dạng: .xlsx, .xls, .csv
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
