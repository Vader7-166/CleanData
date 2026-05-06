import { Wand2 } from "lucide-react";

export function DictionaryGenerator() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="mb-2">Dictionary Generator</h2>
        <p className="text-muted-foreground">
          Công cụ tự động tạo từ điển từ dữ liệu
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <div className="bg-card border border-border rounded-lg p-12 text-center">
          <div className="w-20 h-20 rounded-full bg-muted mx-auto mb-6 flex items-center justify-center">
            <Wand2 className="w-10 h-10 text-muted-foreground" />
          </div>
          <h3 className="mb-2">Tính năng đang phát triển</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            Công cụ tạo từ điển tự động sẽ sớm được ra mắt. Bạn có thể phân tích
            dữ liệu và tạo từ điển chuẩn hóa một cách tự động.
          </p>
        </div>
      </div>
    </div>
  );
}
