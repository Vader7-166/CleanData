import { Download, CheckCircle, Circle } from "lucide-react";

const mockDictionaries = [
  {
    id: 1,
    name: "Từ điển địa chỉ Việt Nam",
    description: "Chuẩn hóa tên tỉnh, thành phố, quận, huyện",
    entries: 1234,
    active: true,
    lastUpdated: "2026-04-15",
  },
  {
    id: 2,
    name: "Từ điển tên công ty",
    description: "Chuẩn hóa tên doanh nghiệp và công ty",
    entries: 5678,
    active: false,
    lastUpdated: "2026-03-20",
  },
  {
    id: 3,
    name: "Từ điển ngành nghề",
    description: "Phân loại và chuẩn hóa ngành nghề kinh doanh",
    entries: 892,
    active: true,
    lastUpdated: "2026-05-01",
  },
];

export function Dictionary() {
  return (
    <div className="p-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="mb-2">Dictionary</h2>
          <p className="text-muted-foreground">
            Quản lý các từ điển để chuẩn hóa dữ liệu
          </p>
        </div>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors">
          Tạo từ điển mới
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockDictionaries.map((dict) => (
          <div
            key={dict.id}
            className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <h3>{dict.name}</h3>
              <button
                className={`p-1 rounded-full transition-colors ${
                  dict.active
                    ? "text-green-600 hover:bg-green-50"
                    : "text-muted-foreground hover:bg-accent"
                }`}
              >
                {dict.active ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <Circle className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-muted-foreground mb-4">{dict.description}</p>
            <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
              <span>{dict.entries.toLocaleString()} mục</span>
              <span>Cập nhật: {dict.lastUpdated}</span>
            </div>
            <div className="flex gap-2">
              <button className="flex-1 bg-secondary text-secondary-foreground px-3 py-2 rounded-md hover:bg-secondary/80 transition-colors">
                {dict.active ? "Hủy kích hoạt" : "Kích hoạt"}
              </button>
              <button className="px-3 py-2 border border-border rounded-md hover:bg-accent transition-colors">
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
