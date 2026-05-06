import { Download, Trash2, Eye } from "lucide-react";

const mockData = [
  {
    id: 1,
    name: "Sales_Data_Q1_2026.xlsx",
    status: "Completed",
    date: "2026-05-01",
    rows: 15234,
    cleaned: 14892,
  },
  {
    id: 2,
    name: "Customer_List_April.xlsx",
    status: "Completed",
    date: "2026-04-28",
    rows: 8921,
    cleaned: 8654,
  },
  {
    id: 3,
    name: "Inventory_Data.xlsx",
    status: "Processing",
    date: "2026-05-06",
    rows: 22341,
    cleaned: 18234,
  },
];

export function Dashboard() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="mb-2">Dashboard</h2>
        <p className="text-muted-foreground">
          Tổng quan về các tệp dữ liệu đã xử lý
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-muted-foreground mb-2">Tổng số tệp</div>
          <div className="text-3xl">{mockData.length}</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-muted-foreground mb-2">Đã hoàn thành</div>
          <div className="text-3xl">
            {mockData.filter((d) => d.status === "Completed").length}
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-muted-foreground mb-2">Tổng số dòng</div>
          <div className="text-3xl">
            {mockData.reduce((acc, d) => acc + d.rows, 0).toLocaleString()}
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-lg">
        <div className="p-6 border-b border-border">
          <h3>Danh sách tệp đã xử lý</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-border">
              <tr>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Tên tệp
                </th>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Trạng thái
                </th>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Ngày xử lý
                </th>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Dòng gốc
                </th>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Đã làm sạch
                </th>
                <th className="text-left p-4 text-muted-foreground font-medium">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody>
              {mockData.map((item) => (
                <tr key={item.id} className="border-b border-border last:border-0">
                  <td className="p-4">{item.name}</td>
                  <td className="p-4">
                    <span
                      className={`inline-flex px-2 py-1 rounded-md ${
                        item.status === "Completed"
                          ? "bg-green-100 text-green-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {item.status === "Completed" ? "Hoàn thành" : "Đang xử lý"}
                    </span>
                  </td>
                  <td className="p-4">{item.date}</td>
                  <td className="p-4">{item.rows.toLocaleString()}</td>
                  <td className="p-4">{item.cleaned.toLocaleString()}</td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <button className="p-2 hover:bg-accent rounded-md transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 hover:bg-accent rounded-md transition-colors">
                        <Download className="w-4 h-4" />
                      </button>
                      <button className="p-2 hover:bg-destructive/10 text-destructive rounded-md transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
