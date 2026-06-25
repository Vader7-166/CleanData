import React, { useState } from 'react';
import { BrainCircuit, Play, CheckCircle, AlertCircle, Loader2, Info } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const KnowledgeUpdate = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{status: string, message: string} | null>(null);

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
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-primary flex items-center justify-center gap-3">
          <BrainCircuit className="w-8 h-8" />
          Cập Nhật Tri Thức AI
        </h2>
        <p className="text-muted-foreground text-lg">
          Hệ thống sẽ tự động đọc các file "HQ" mới nhất trong máy chủ để cập nhật dữ liệu.
        </p>
      </div>

      <Card className="border-2 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 p-32 bg-primary/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
        <CardContent className="p-8 md:p-12 text-center relative z-10">
          <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-8 relative">
            {loading && <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>}
            <BrainCircuit className={`w-12 h-12 text-primary ${loading ? 'animate-pulse' : ''}`} />
          </div>

          <div className="max-w-xl mx-auto space-y-8">
            <div>
              <h3 className="text-2xl font-bold mb-3">Sẵn sàng cho AI học dữ liệu mới?</h3>
              <p className="text-muted-foreground text-base">
                Quá trình này sẽ tốn khoảng <strong>1-2 phút</strong>. Hãy đảm bảo bạn đã chép file Excel nghiệp vụ mới (vd: HQ2026.xlsx) vào thư mục <code className="bg-muted px-2 py-1 rounded">CleanData/Filexlsx</code> trên máy chủ.
              </p>
            </div>

            <Button 
              size="lg" 
              onClick={handleLearn} 
              disabled={loading} 
              className="text-lg px-10 h-14 bg-indigo-600 hover:bg-indigo-700 shadow-lg shadow-indigo-600/20"
            >
              {loading ? (
                <>
                  <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                  AI Đang Học (Vui lòng chờ)...
                </>
              ) : (
                <>
                  <Play className="w-6 h-6 mr-3" />
                  Bắt Đầu Cập Nhật
                </>
              )}
            </Button>

            {result && result.status === 'success' && (
              <div className="bg-emerald-500/10 text-emerald-700 p-6 rounded-xl border border-emerald-500/20 flex flex-col items-center gap-3 animate-in fade-in zoom-in duration-300">
                <CheckCircle className="w-10 h-10 text-emerald-500" />
                <h4 className="font-bold text-xl">Thành công tuyệt vời!</h4>
                <p className="text-center">Hệ thống đã nạp file HQ mới, xây dựng lại Từ Điển Vàng và huấn luyện xong AI mô hình dự báo.</p>
              </div>
            )}

            {result && result.status === 'error' && (
              <div className="bg-destructive/10 text-destructive p-6 rounded-xl border border-destructive/20 flex flex-col items-center gap-3 animate-in fade-in zoom-in duration-300">
                <AlertCircle className="w-10 h-10" />
                <h4 className="font-bold text-xl">Đã có lỗi xảy ra</h4>
                <p className="text-center">{result.message}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-6 flex gap-4 items-start">
          <Info className="w-6 h-6 text-blue-600 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h4 className="font-bold text-blue-900">Khi nào nên chạy chức năng này?</h4>
            <p className="text-blue-800/80">
              Bạn chỉ cần chạy chức năng này khi có <strong>sản phẩm mới</strong> (những sản phẩm bị phân loại vào Sheet Cần Nghiệp Vụ) và bạn đã bổ sung thủ công phân loại của chúng vào một file Excel HQ (HQ2027 v.v.). Sau khi AI "học" xong, lần tới các sản phẩm đó sẽ được hệ thống Tự Động Duyệt.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default KnowledgeUpdate;
