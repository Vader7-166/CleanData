import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Pencil, Trash2, Upload, Search, Database, RefreshCw, X, Save } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TaxonomyRecord {
  id: number;
  hs_code_prefix: string;
  dong_sp: string;
  industry_name: string;
  default_type: string;
  source: string;
  created_at: string;
  updated_at: string;
}

const DONG_SP_OPTIONS = [
  'SP BÌNH/PHÍCH',
  'SP THỦY TINH',
  'SP ĐÈN/BÓNG ĐÈN',
  'SP ĐÈN/THIẾT BỊ CHIẾU SÁNG',
  'SP THIẾT BỊ ĐIỆN GIA DỤNG',
];

const HSTaxonomy: React.FC = () => {
  const [records, setRecords] = useState<TaxonomyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editRecord, setEditRecord] = useState<TaxonomyRecord | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form fields
  const [formHsCode, setFormHsCode] = useState('');
  const [formDongSp, setFormDongSp] = useState('');
  const [formIndustryName, setFormIndustryName] = useState('');
  const [formDefaultType, setFormDefaultType] = useState('NC');

  // Quick lookup state
  const [lookupHsCode, setLookupHsCode] = useState('');
  const [lookupResult, setLookupResult] = useState<{
    hs_code: string;
    dong_sp: string;
    industry_name: string;
    default_type: string;
    source: string;
  } | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');

  // Dialog lookup state
  const [dialogLookupLoading, setDialogLookupLoading] = useState(false);
  const [dialogLookupError, setDialogLookupError] = useState('');

  const token = localStorage.getItem('token');

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/taxonomy`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setRecords(data.taxonomy || []);
      }
    } catch {
      setError('Không thể tải danh sách HS Taxonomy.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const openAddDialog = () => {
    setEditRecord(null);
    setFormHsCode('');
    setFormDongSp('');
    setFormIndustryName('');
    setFormDefaultType('NC');
    setDialogOpen(true);
    setError('');
    setDialogLookupError('');
  };

  const openEditDialog = (record: TaxonomyRecord) => {
    setEditRecord(record);
    setFormHsCode(record.hs_code_prefix);
    setFormDongSp(record.dong_sp);
    setFormIndustryName(record.industry_name);
    setFormDefaultType(record.default_type);
    setDialogOpen(true);
    setError('');
    setDialogLookupError('');
  };

  const handleSave = async () => {
    setError('');
    try {
      if (editRecord) {
        const res = await fetch(`${API_URL}/api/taxonomy/${editRecord.id}`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dong_sp: formDongSp,
            industry_name: formIndustryName,
            default_type: formDefaultType,
          }),
        });
        if (!res.ok) {
          const d = await res.json();
          setError(d.detail || 'Cập nhật thất bại.');
          return;
        }
        setSuccess('Cập nhật thành công!');
      } else {
        const res = await fetch(`${API_URL}/api/taxonomy`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            hs_code_prefix: formHsCode,
            dong_sp: formDongSp,
            industry_name: formIndustryName,
            default_type: formDefaultType,
          }),
        });
        if (!res.ok) {
          const d = await res.json();
          setError(d.detail || 'Thêm mới thất bại.');
          return;
        }
        setSuccess('Thêm mới thành công!');
      }
      setDialogOpen(false);
      fetchRecords();
      setTimeout(() => setSuccess(''), 3000);
    } catch {
      setError('Đã xảy ra lỗi khi lưu.');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/api/taxonomy/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSuccess('Đã xóa thành công!');
        fetchRecords();
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch {
      setError('Xóa thất bại.');
    }
    setDeleteConfirm(null);
  };

  const handleBulkUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/api/taxonomy/bulk-upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(`Import thành công ${data.count} bản ghi.`);
        fetchRecords();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(data.detail || 'Import thất bại.');
      }
    } catch {
      setError('Đã xảy ra lỗi khi import.');
    }
    e.target.value = '';
  };

  const handleQuickLookup = async () => {
    if (!lookupHsCode.trim()) return;
    setLookupLoading(true);
    setLookupError('');
    setLookupResult(null);

    try {
      const res = await fetch(`${API_URL}/api/taxonomy/check-hs-codes`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hs_codes: [lookupHsCode.trim()] }),
      });

      if (!res.ok) {
        throw new Error('Không thể kết nối đến máy chủ.');
      }

      const data = await res.json();
      if (data.resolved && data.resolved.length > 0) {
        setLookupResult(data.resolved[0]);
        fetchRecords();
      } else {
        setLookupError('Không tìm thấy thông tin cho mã HS này. Hãy tự thêm thủ công.');
      }
    } catch (err: any) {
      setLookupError(err.message || 'Đã xảy ra lỗi khi tra cứu.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleDialogLookup = async () => {
    if (!formHsCode.trim()) return;
    setDialogLookupLoading(true);
    setDialogLookupError('');

    try {
      const res = await fetch(`${API_URL}/api/taxonomy/check-hs-codes`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hs_codes: [formHsCode.trim()] }),
      });

      if (!res.ok) {
        throw new Error('Không thể kết nối đến máy chủ.');
      }

      const data = await res.json();
      if (data.resolved && data.resolved.length > 0) {
        const item = data.resolved[0];
        setFormDongSp(item.dong_sp || '');
        setFormIndustryName(item.industry_name || '');
        setFormDefaultType(item.default_type || 'NC');
        fetchRecords();
      } else {
        setDialogLookupError('Không tìm thấy thông tin tự động. Vui lòng tự nhập tay.');
      }
    } catch (err: any) {
      setDialogLookupError(err.message || 'Đã xảy ra lỗi khi tra cứu.');
    } finally {
      setDialogLookupLoading(false);
    }
  };

  const filtered = records.filter(
    (r) =>
      r.hs_code_prefix.includes(search) ||
      r.industry_name.toLowerCase().includes(search.toLowerCase()) ||
      r.dong_sp.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Database className="text-primary" />
            HS Taxonomy Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Quản lý danh mục mã HS, dòng sản phẩm và phân loại NC/LK.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <label className="cursor-pointer gap-2">
              <Upload className="size-4" />
              Import CSV
              <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleBulkUpload} />
            </label>
          </Button>
          <Button size="sm" onClick={openAddDialog} className="gap-2">
            <Plus className="size-4" />
            Thêm mới
          </Button>
        </div>
      </div>

      {success && (
        <div className="bg-green-500/10 text-green-600 p-3 rounded-md text-sm border border-green-500/20">{success}</div>
      )}
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm border border-destructive/20">{error}</div>
      )}

      {/* Quick Lookup Card */}
      <Card className="border border-primary/20 bg-primary/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="size-5 text-primary" />
            Tra cứu nhanh mã HS tự động (Hải quan / AI)
          </CardTitle>
          <CardDescription>
            Nhập mã HS để hệ thống tự động tìm kiếm trong cơ sở dữ liệu hoặc cào thông tin và phân loại trực tiếp.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 max-w-md">
            <Input
              placeholder="Nhập mã HS (ví dụ: 85395210)"
              value={lookupHsCode}
              onChange={(e) => setLookupHsCode(e.target.value.replace(/\D/g, ''))}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleQuickLookup();
              }}
              className="font-mono"
            />
            <Button onClick={handleQuickLookup} disabled={lookupLoading || !lookupHsCode} className="gap-2 shrink-0">
              {lookupLoading ? (
                <RefreshCw className="size-4 animate-spin" />
              ) : (
                <Search className="size-4" />
              )}
              Tra cứu
            </Button>
          </div>

          {lookupError && (
            <p className="text-sm text-destructive mt-3 font-medium flex items-center gap-1.5 animate-in fade-in duration-200">
              <span className="inline-block w-1.5 h-1.5 bg-destructive rounded-full" />
              {lookupError}
            </p>
          )}

          {lookupResult && (
            <div className="mt-4 p-4 rounded-lg bg-background border border-border space-y-3 max-w-2xl animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-muted-foreground">Mã HS:</span>
                  <span className="font-mono font-bold text-foreground text-lg">{lookupResult.hs_code}</span>
                </div>
                <div className="flex gap-1.5">
                  <Badge variant={lookupResult.default_type === 'NC' ? 'default' : 'secondary'}>
                    {lookupResult.default_type === 'NC' ? 'Nguyên chiếc (NC)' : 'Linh kiện (LK)'}
                  </Badge>
                  <Badge variant="outline" className="capitalize">
                    Nguồn: {lookupResult.source === 'crawled' ? 'Cào Hải quan + AI' : lookupResult.source}
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="block text-xs font-medium text-muted-foreground mb-0.5">Dòng sản phẩm:</span>
                  <span className="font-semibold text-foreground">{lookupResult.dong_sp || '-'}</span>
                </div>
                <div>
                  <span className="block text-xs font-medium text-muted-foreground mb-0.5">Lớp 1 (Tên ngành):</span>
                  <span className="font-semibold text-foreground">{lookupResult.industry_name || '-'}</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b bg-muted/30">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Danh sách mã HS ({filtered.length})</CardTitle>
              <CardDescription>Tìm kiếm theo mã HS, tên ngành hàng hoặc dòng sản phẩm</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                <Input
                  placeholder="Tìm kiếm..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <Button variant="ghost" size="icon" onClick={fetchRecords} disabled={loading}>
                <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mã HS</TableHead>
                <TableHead>Dòng SP</TableHead>
                <TableHead>Lớp 1 (Tên ngành)</TableHead>
                <TableHead>Loại</TableHead>
                <TableHead>Nguồn</TableHead>
                <TableHead>Cập nhật</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    {loading ? 'Đang tải...' : 'Không có dữ liệu.'}
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono font-semibold">{r.hs_code_prefix}</TableCell>
                    <TableCell>{r.dong_sp}</TableCell>
                    <TableCell className="max-w-xs truncate">{r.industry_name}</TableCell>
                    <TableCell>
                      <Badge variant={r.default_type === 'NC' ? 'default' : 'secondary'}>
                        {r.default_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {r.source}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {r.updated_at ? new Date(r.updated_at).toLocaleDateString('vi-VN') : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="size-8" onClick={() => openEditDialog(r)}>
                          <Pencil className="size-3.5" />
                        </Button>
                        {deleteConfirm === r.id ? (
                          <div className="flex gap-1">
                            <Button variant="destructive" size="icon" className="size-8" onClick={() => handleDelete(r.id)}>
                              <Trash2 className="size-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon" className="size-8" onClick={() => setDeleteConfirm(null)}>
                              <X className="size-3.5" />
                            </Button>
                          </div>
                        ) : (
                          <Button variant="ghost" size="icon" className="size-8 text-destructive hover:text-destructive" onClick={() => setDeleteConfirm(r.id)}>
                            <Trash2 className="size-3.5" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg text-foreground">
          <DialogHeader>
            <DialogTitle>{editRecord ? 'Chỉnh sửa mã HS' : 'Thêm mã HS mới'}</DialogTitle>
            <DialogDescription>
              {editRecord ? 'Cập nhật thông tin cho mã HS này.' : 'Nhập thông tin phân loại cho mã HS mới.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Mã HS</label>
              <div className="flex gap-2">
                <Input
                  value={formHsCode}
                  onChange={(e) => setFormHsCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="Ví dụ: 85395210"
                  disabled={!!editRecord}
                  className="font-mono"
                />
                {!editRecord && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleDialogLookup}
                    disabled={dialogLookupLoading || !formHsCode}
                    className="gap-1.5 shrink-0"
                  >
                    {dialogLookupLoading ? (
                      <RefreshCw className="size-4 animate-spin" />
                    ) : (
                      <Search className="size-4" />
                    )}
                    Tra cứu tự động
                  </Button>
                )}
              </div>
              {dialogLookupError && (
                <p className="text-xs text-destructive font-medium mt-1 animate-in fade-in duration-200">{dialogLookupError}</p>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Dòng sản phẩm</label>
              <Input
                value={formDongSp}
                onChange={(e) => setFormDongSp(e.target.value)}
                placeholder="Ví dụ: SP BÓNG ĐÈN ĐIỆN DÂY TÓC"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Lớp 1 (Tên ngành hàng)</label>
              <Input
                value={formIndustryName}
                onChange={(e) => setFormIndustryName(e.target.value)}
                placeholder="Ví dụ: Bóng đèn LED - đầu đèn ren xoáy"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Phân loại</label>
              <Select value={formDefaultType} onValueChange={setFormDefaultType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NC">NC (Nguyên chiếc)</SelectItem>
                  <SelectItem value="LK">LK (Linh kiện)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Hủy</Button>
            <Button onClick={handleSave} className="gap-2" disabled={!formHsCode || !formIndustryName}>
              <Save className="size-4" />
              {editRecord ? 'Cập nhật' : 'Thêm mới'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HSTaxonomy;
