import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Download, FileText, PieChart as PieChartIcon, Loader2, AlertCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const COLORS = ['#00A651', '#1E2A4F', '#E32636', '#0ea5e9', '#f59e0b', '#8b5cf6'];

export default function BatchPreviewDialog({ batchId }: { batchId: string }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Data state
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  
  // Filter & Pagination state
  const [showOnlyReview, setShowOnlyReview] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [showOnlyReview, searchQuery]);

  useEffect(() => {
    if (open) {
      fetchData();
    }
  }, [open]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      
      // Fetch insights
      const insightsRes = await fetch(`${API_URL}/api/batches/${batchId}/insights`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (insightsRes.ok) {
        setInsights(await insightsRes.json());
      }
      
      // We don't have a consolidated preview API yet, so we'll fetch batch status to get jobs
      // then fetch preview for the first job (or all if small). For now, we'll implement a mock
      // or just show the insights.
      // Wait, let's implement a real fetch if needed, but since we didn't add an API for consolidated preview,
      // I'll add it to main.py or just use individual previews and merge them.
      
      const batchRes = await fetch(`${API_URL}/api/batches/${batchId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (batchRes.ok) {
        const batchData = await batchRes.json();
        const jobs = batchData.jobs.filter((j: any) => j.status === 'done');
        const fetchPromises = jobs.map(async (job: any) => {
          const prevRes = await fetch(`${API_URL}/api/jobs/${job.id}/preview?limit=50`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (prevRes.ok) {
            const pd = await prevRes.json();
            return pd.preview.map((r: any) => ({
              ...r,
              'Tên file nguồn': job.filename
            }));
          }
          return [];
        });

        const results = await Promise.all(fetchPromises);
        const allRows = results.flat();
        
        setPreviewData(allRows);
      }
      
    } catch (err: any) {
      setError(err.message || 'Failed to load preview data');
    } finally {
      setLoading(false);
    }
  };

  const filteredData = previewData.filter(row => {
    if (showOnlyReview && row['Trạng Thái'] !== 'Cần kiểm tra') return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return Object.values(row).some(v => String(v).toLowerCase().includes(q));
    }
    return true;
  });

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const paginatedData = filteredData.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const allKeys = Array.from(new Set(filteredData.flatMap(row => Object.keys(row))));

  const downloadMerged = () => {
    window.location.href = `${API_URL}/api/batches/${batchId}/download-merged?token=${localStorage.getItem('token')}`;
  };

  const downloadZip = () => {
    window.location.href = `${API_URL}/api/batches/${batchId}/download-zip?token=${localStorage.getItem('token')}`;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default">
          <PieChartIcon className="mr-2 size-4" /> View Insights & Preview
        </Button>
      </DialogTrigger>
      
      <DialogContent className="!max-w-[95vw] w-full h-[95vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Batch Insights & Data Preview</DialogTitle>
          <DialogDescription>
            Review consolidated data across all processed files in this batch.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
            <Loader2 className="size-10 animate-spin text-primary" />
            <p className="text-muted-foreground">Loading batch data...</p>
          </div>
        ) : error ? (
          <div className="p-6 bg-red-50 text-red-600 rounded-lg flex items-center gap-3">
            <AlertCircle /> <p>{error}</p>
          </div>
        ) : (
          <Tabs defaultValue="insights" className="flex-1 flex flex-col overflow-hidden mt-4">
            <div className="flex justify-between items-center mb-4">
              <TabsList>
                <TabsTrigger value="insights">Market Insights</TabsTrigger>
                <TabsTrigger value="preview">Data Preview</TabsTrigger>
              </TabsList>
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" onClick={downloadZip}>
                  <Download className="mr-2 size-4" /> Tải tất cả (ZIP)
                </Button>
                <Button variant="default" size="sm" onClick={downloadMerged}>
                  <Download className="mr-2 size-4" /> Tải file gộp (Excel)
                </Button>
              </div>
            </div>

            <TabsContent value="insights" className="flex-1 overflow-auto border rounded-lg p-6 bg-slate-50/50 m-0">
              {insights && (
                <div className="flex flex-col gap-8">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-6 rounded-xl border shadow-sm flex flex-col justify-center items-center">
                      <h4 className="text-muted-foreground font-medium mb-2">Tổng Số Dòng Dữ Liệu</h4>
                      <p className="text-4xl font-bold text-primary">{insights.total_rows?.toLocaleString() || 0}</p>
                    </div>
                    <div className="bg-white p-6 rounded-xl border shadow-sm flex flex-col justify-center items-center">
                      <h4 className="text-muted-foreground font-medium mb-2">Tỷ lệ Tự động Hoàn thành</h4>
                      <div className="flex items-end gap-2">
                        <p className="text-4xl font-bold text-green-600">
                          {insights.total_rows ? (((insights.total_rows - (insights.needs_review_count || 0)) / insights.total_rows) * 100).toFixed(1) : 0}%
                        </p>
                        <p className="text-sm text-muted-foreground mb-1">
                          ({insights.needs_review_count || 0} dòng cần kiểm tra)
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Product Lines Chart */}
                    <div className="bg-white p-4 rounded-xl border shadow-sm">
                      <h3 className="font-semibold text-center mb-4">Phân bổ Dòng Sản Phẩm</h3>
                      <div className="h-64">
                        {insights.product_lines?.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                              <Pie
                                data={insights.product_lines}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                                label={({name, percent}) => {
                                  const tName = name.length > 15 ? name.substring(0, 15) + '...' : name;
                                  return `${tName} ${(percent * 100).toFixed(0)}%`;
                                }}
                              >
                                {insights.product_lines.map((entry: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(value: number) => [value, 'Số lượng']} />
                            </PieChart>
                          </ResponsiveContainer>
                        ) : <p className="text-center text-muted-foreground pt-20">Không có dữ liệu</p>}
                      </div>
                    </div>

                    {/* Top HS Codes Chart */}
                    <div className="bg-white p-4 rounded-xl border shadow-sm">
                      <h3 className="font-semibold text-center mb-4">Top 5 Lớp 1 (Mã HS)</h3>
                      <div className="h-64">
                        {insights.top_hs_codes?.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                              <Pie
                                data={insights.top_hs_codes}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                dataKey="value"
                                label={({name, percent}) => {
                                  const tName = name.length > 15 ? name.substring(0, 15) + '...' : name;
                                  return `${tName} ${(percent * 100).toFixed(0)}%`;
                                }}
                              >
                                {insights.top_hs_codes.map((entry: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(value: number) => [value, 'Số lượng']} />
                            </PieChart>
                          </ResponsiveContainer>
                        ) : <p className="text-center text-muted-foreground pt-20">Không có dữ liệu</p>}
                      </div>
                    </div>

                    {/* Top Companies Bar Chart */}
                    <div className="md:col-span-2 bg-white p-4 rounded-xl border shadow-sm">
                      <h3 className="font-semibold text-center mb-4">Top 5 Công ty theo Giá trị</h3>
                      <div className="h-72">
                        {insights.top_companies?.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={insights.top_companies} layout="vertical" margin={{ top: 10, right: 30, left: 50, bottom: 10 }}>
                              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                              <XAxis type="number" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                              <YAxis type="category" dataKey="name" width={150} tick={{fontSize: 11}} tickFormatter={(v) => v.length > 20 ? v.substring(0, 20) + '...' : v} />
                              <Tooltip cursor={{fill: '#f5f5f5'}} formatter={(value: number) => [`$${value.toLocaleString()}`, 'Giá trị']} labelFormatter={(l) => l} />
                              <Bar dataKey="value" fill="#00A651" radius={[0, 4, 4, 0]}>
                                {insights.top_companies.map((entry: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        ) : <p className="text-center text-muted-foreground pt-20">Không có dữ liệu</p>}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="preview" className="flex-1 flex flex-col overflow-hidden m-0 border rounded-lg">
              <div className="p-4 bg-muted/30 border-b flex flex-wrap gap-4 items-center justify-between">
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <Switch 
                      id="review-mode" 
                      checked={showOnlyReview} 
                      onCheckedChange={setShowOnlyReview} 
                    />
                    <Label htmlFor="review-mode" className="font-medium cursor-pointer">
                      Chỉ hiển thị dòng "Cần kiểm tra"
                    </Label>
                  </div>
                  <div className="relative w-64">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Tìm kiếm..."
                      className="pl-9 bg-white"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
                <div className="text-sm text-muted-foreground flex items-center gap-2">
                  <FileText className="size-4" />
                  Kết quả: {filteredData.length} dòng
                </div>
              </div>

              <div className="flex-1 overflow-auto">
                {paginatedData.length > 0 ? (
                  <Table className="relative">
                    <TableHeader className="sticky top-0 bg-background z-10 border-b shadow-sm">
                      <TableRow>
                        {allKeys.map(col => (
                          <TableHead key={col} className={`whitespace-nowrap ${col === 'Tên file nguồn' ? 'bg-primary/5 font-bold' : ''}`}>
                            {col}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedData.map((row, i) => (
                        <TableRow key={`row-${i}`} className={row['Trạng Thái'] === 'Cần kiểm tra' ? 'bg-amber-50/50' : ''}>
                          {allKeys.map(col => (
                            <TableCell key={`cell-${i}-${col}`} className={`whitespace-nowrap max-w-[250px] truncate ${col === 'Tên file nguồn' ? 'bg-primary/5 font-medium text-xs' : ''}`}>
                              {col === 'Trạng Thái' ? (
                                <Badge variant={row[col] === 'Cần kiểm tra' ? 'destructive' : 'default'} className={row[col] === 'Hoàn thành' ? 'bg-green-600 hover:bg-green-700' : ''}>
                                  {row[col]}
                                </Badge>
                              ) : row[col] !== undefined ? row[col] : ''}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="p-12 text-center text-muted-foreground">
                    Không có dữ liệu phù hợp với điều kiện lọc.
                  </div>
                )}
              </div>
              
              {/* Pagination Footer */}
              {totalPages > 1 && (
                <div className="p-3 border-t bg-muted/20 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Trang {currentPage} / {totalPages}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="size-4 mr-1" /> Trước
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Sau <ChevronRight className="size-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
