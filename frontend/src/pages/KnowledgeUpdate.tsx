import React, { useState, useEffect, useRef } from 'react';
import { BrainCircuit, Play, CheckCircle, AlertCircle, Loader2, Info, UploadCloud, FileSpreadsheet, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HQFile {
  filename: string;
  size: number;
  updated_at: number;
}

const KnowledgeUpdate = () => {
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{status: string, message: string} | null>(null);
  const [files, setFiles] = useState<HQFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/api/hq-files`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      if (response.ok) {
        setFiles(data.files || []);
      }
    } catch (err) {
      console.error('Failed to fetch HQ files', err);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    setUploading(true);
    setResult(null);
    
    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append('files', selectedFiles[i]);
    }

    try {
      const response = await fetch(`${API_URL}/api/upload-hq`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || data.detail || 'Lỗi tải file');
      }
      
      setResult({ status: 'success', message: data.message });
      fetchFiles();
    } catch (err: any) {
      setResult({ status: 'error', message: err.message });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteFile = async (filename: string) => {
    if (!window.confirm(`Bạn có chắc muốn xóa file ${filename}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/hq-files/${filename}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        fetchFiles();
      } else {
        const data = await response.json();
        alert(data.detail || 'Lỗi khi xóa file');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLearn = async () => {
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/api/learn`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      const data = await response.json();
      if (!response.ok || data.status === 'error') {
        throw new Error(data.message || data.detail || 'Lỗi hệ thống khi cập nhật tri thức.');
      }
      
      setResult({ status: 'success', message: data.message });
    } catch (err: any) {
      setResult({ status: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-10">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-primary flex items-center justify-center gap-3">
          <BrainCircuit className="w-8 h-8" />
          Cập Nhật Tri Thức AI
        </h2>
        <p className="text-muted-foreground text-lg">
          Quản lý các file chuẩn nghiệp vụ (HQ) và huấn luyện lại hệ thống AI
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cột 1: Tải file lên */}
        <Card className="border-2 shadow-sm relative overflow-hidden flex flex-col">
          <div className="absolute top-0 right-0 p-32 bg-indigo-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
          <CardContent className="p-6 relative z-10 flex-1 flex flex-col">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <UploadCloud className="w-6 h-6 text-indigo-500" />
              1. Tải lên File Nghiệp Vụ
            </h3>
            <p className="text-muted-foreground text-sm mb-6">
              Chọn các file Excel chứa dữ liệu đã được nghiệp vụ duyệt chuẩn xác để bổ sung vào từ điển của hệ thống.
            </p>
            
            <div 
              className="border-2 border-dashed border-indigo-200 bg-indigo-50/50 rounded-xl p-8 text-center flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                type="file" 
                multiple 
                accept=".xlsx,.xls" 
                className="hidden" 
                ref={fileInputRef}
                onChange={handleFileUpload}
              />
              <UploadCloud className="w-12 h-12 text-indigo-300 mb-4" />
              <p className="font-semibold text-indigo-700">Nhấp để chọn file Excel (.xlsx)</p>
              <p className="text-xs text-indigo-500/70 mt-2">Hỗ trợ chọn nhiều file cùng lúc</p>
              
              {uploading && (
                <div className="mt-4 flex items-center text-sm text-indigo-600 font-medium">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Đang tải lên...
                </div>
              )}
            </div>

            <div className="mt-6">
              <h4 className="text-sm font-semibold mb-3 flex items-center justify-between">
                <span>File hiện có trong hệ thống:</span>
                <span className="bg-indigo-100 text-indigo-700 py-0.5 px-2 rounded-full text-xs">{files.length} file</span>
              </h4>
              <div className="space-y-2 max-h-[150px] overflow-y-auto pr-2 custom-scrollbar">
                {files.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic text-center py-4 bg-muted/30 rounded-lg">Chưa có file nào.</p>
                ) : (
                  files.map((f) => (
                    <div key={f.filename} className="flex items-center justify-between p-2 rounded-md bg-muted/50 text-sm group hover:bg-muted transition-colors">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <FileSpreadsheet className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span className="truncate" title={f.filename}>{f.filename}</span>
                      </div>
                      <button 
                        onClick={() => handleDeleteFile(f.filename)}
                        className="text-destructive/50 hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity p-1"
                        title="Xóa file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cột 2: Học dữ liệu */}
        <Card className="border-2 shadow-sm relative overflow-hidden flex flex-col">
          <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
          <CardContent className="p-6 relative z-10 flex-1 flex flex-col">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <BrainCircuit className="w-6 h-6 text-emerald-500" />
              2. Bắt Đầu Cập Nhật
            </h3>
            <p className="text-muted-foreground text-sm mb-6">
              AI sẽ quét toàn bộ các file ở bước 1, tự động gộp, tinh lọc để xây dựng lại Từ Điển Vàng và huấn luyện lại Mô Hình Nhận Diện.
            </p>

            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="w-20 h-20 rounded-full bg-emerald-50 flex items-center justify-center mb-6 relative">
                {loading && <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>}
                <BrainCircuit className={`w-10 h-10 text-emerald-600 ${loading ? 'animate-pulse' : ''}`} />
              </div>

              <Button 
                size="lg" 
                onClick={handleLearn} 
                disabled={loading || files.length === 0} 
                className="w-full text-lg h-14 bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-600/20"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                    Đang Học (1-2 phút)...
                  </>
                ) : (
                  <>
                    <Play className="w-6 h-6 mr-3" />
                    Huấn Luyện AI
                  </>
                )}
              </Button>
              {files.length === 0 && (
                <p className="text-xs text-destructive mt-3 text-center">Vui lòng tải lên ít nhất 1 file HQ để huấn luyện</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {result && result.status === 'success' && (
        <div className="bg-emerald-500/10 text-emerald-700 p-6 rounded-xl border border-emerald-500/20 flex items-center gap-4 animate-in fade-in zoom-in duration-300">
          <CheckCircle className="w-10 h-10 text-emerald-500 shrink-0" />
          <div>
            <h4 className="font-bold text-xl mb-1">Thành công tuyệt vời!</h4>
            <p>{result.message || 'Hệ thống đã nạp file HQ mới, xây dựng lại Từ Điển Vàng và huấn luyện xong AI mô hình dự báo.'}</p>
          </div>
        </div>
      )}

      {result && result.status === 'error' && (
        <div className="bg-destructive/10 text-destructive p-6 rounded-xl border border-destructive/20 flex items-center gap-4 animate-in fade-in zoom-in duration-300">
          <AlertCircle className="w-10 h-10 shrink-0" />
          <div>
            <h4 className="font-bold text-xl mb-1">Đã có lỗi xảy ra</h4>
            <p>{result.message}</p>
          </div>
        </div>
      )}
      
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-6 flex gap-4 items-start">
          <Info className="w-6 h-6 text-blue-600 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h4 className="font-bold text-blue-900">Quy trình làm việc chuẩn</h4>
            <p className="text-blue-800/80 text-sm leading-relaxed">
              1. Tải lên (hoặc bổ sung thêm) các file Excel nghiệp vụ (ví dụ: <span className="font-mono bg-blue-100 px-1 rounded">HQ2025.xlsx</span>) ở cột bên trái.<br/>
              2. Nhấn nút <strong>Huấn Luyện AI</strong> ở cột bên phải để hệ thống đồng bộ dữ liệu mới.<br/>
              3. Lần tới, khi bạn làm sạch file raw, AI sẽ nhớ tất cả những tri thức mới này để Tự Động Duyệt thay vì đẩy ra Sheet Cần Nghiệp Vụ.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default KnowledgeUpdate;
