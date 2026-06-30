import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, Download, RefreshCw, CheckCircle, AlertCircle, Sparkles, FileSpreadsheet, Loader2 } from 'lucide-react';
import usePersistedState from '../hooks/usePersistedState';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { useFileContext } from '../contexts/FileContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CleanData = () => {
  const { cleanDataFiles: files, setCleanDataFiles: setFiles } = useFileContext();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [activeBatchId, setActiveBatchId] = usePersistedState<string | null>('clean_data_batch_id', null);
  const [batchStatus, setBatchStatus] = useState<any>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (activeBatchId) {
      startPolling(activeBatchId);
    }
    return () => stopPolling();
  }, [activeBatchId]);

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const startPolling = (batchId: string) => {
    stopPolling();
    setLoading(true);
    pollingIntervalRef.current = window.setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/batches/${batchId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.ok) {
          const data = await res.json();
          setBatchStatus(data);
          
          if (data.status === 'done' || data.status === 'error' || data.status === 'cancelled') {
            stopPolling();
            setLoading(false);
          }
        } else {
          stopPolling();
          if (res.status === 404 || res.status === 403 || res.status === 401) {
            setActiveBatchId(null);
            setBatchStatus(null);
            setError('');
          } else {
            setError("Lỗi kết nối khi lấy trạng thái tiến trình.");
          }
          setLoading(false);
        }
      } catch (err) {
        stopPolling();
        setError("Mất kết nối máy chủ, đang thử lại...");
        setLoading(false);
      }
    }, 2000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(selectedFiles);
      setError('');
    }
  };

  const handleProcess = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // Automatically use "auto" for transaction types to hide complexity
    const txTypes: Record<string, string> = {};
    files.forEach(f => { txTypes[f.name] = ""; });
    formData.append('transaction_types', JSON.stringify(txTypes));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng xuất và đăng nhập lại!');
        }
        const err = await response.json();
        throw new Error(err.detail || 'Lỗi khi tải file lên');
      }

      const data = await response.json();
      setActiveBatchId(data.batch_id);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleCancelBatch = async () => {
    if (!activeBatchId) return;
    try {
      const res = await fetch(`${API_URL}/api/batches/${activeBatchId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        resetPage();
      } else {
        setError("Không thể hủy tiến trình.");
      }
    } catch (err) {
      setError("Mất kết nối máy chủ khi hủy tiến trình.");
    }
  };

  const resetPage = () => {
    setFiles([]);
    setBatchStatus(null);
    setError('');
    setActiveBatchId(null);
    stopPolling();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Helper to determine active step
  const getStep = () => {
    if (!activeBatchId && files.length === 0) return 1;
    if (!activeBatchId && files.length > 0) return 2;
    if (activeBatchId && batchStatus?.status !== 'done' && batchStatus?.status !== 'error') return 3;
    if (batchStatus?.status === 'done') return 4;
    return 1;
  };

  const currentStep = getStep();

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-primary">Làm Sạch Dữ Liệu Tự Động</h2>
        <p className="text-muted-foreground text-lg">
          Trí tuệ nhân tạo sẽ tự động phân loại mã HS, chuẩn hóa Tên Hàng và Hãng Sản Xuất.
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-xl border border-destructive/20 flex items-center gap-3">
          <AlertCircle className="size-6" />
          <p className="font-medium text-base">{error}</p>
        </div>
      )}

      {/* Stepper Wizard */}
      <div className="flex items-center justify-center mb-8">
        {[
          { id: 1, name: "Chọn file" },
          { id: 2, name: "Tải lên" },
          { id: 3, name: "AI Xử lý" },
          { id: 4, name: "Hoàn tất" }
        ].map((step, idx) => (
          <div key={step.id} className="flex items-center">
            <div className={`flex flex-col items-center w-24 ${currentStep >= step.id ? "text-primary" : "text-muted-foreground"}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold mb-2 transition-colors duration-300 ${
                currentStep >= step.id ? "bg-primary text-primary-foreground shadow-md" : "bg-muted"
              }`}>
                {step.id}
              </div>
              <span className="text-sm font-medium">{step.name}</span>
            </div>
            {idx < 3 && (
              <div className={`h-1 w-16 mx-2 rounded transition-colors duration-300 ${
                currentStep > step.id ? "bg-primary" : "bg-muted"
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1 & 2: Upload */}
      <AnimatePresence mode="wait">
      {currentStep < 3 && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.4 }}
        >
        <Card className="border-0 shadow-xl bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl">
          <CardContent className="p-8">
            <div 
              className={`border-2 border-dashed rounded-2xl p-16 text-center transition-all duration-300 relative overflow-hidden ${
                files.length > 0 ? "border-primary bg-primary/5 shadow-[0_0_40px_rgba(0,166,81,0.1)]" : "border-slate-300 dark:border-slate-700 hover:border-primary/50 hover:bg-slate-50/50 dark:hover:bg-slate-800/50"
              }`}
            >
              <div className="flex flex-col items-center gap-6">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                  <FileSpreadsheet className="w-10 h-10 text-primary" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">
                    {files.length > 0 ? `Đã chọn ${files.length} file Excel` : "Kéo thả file Excel vào đây"}
                  </h3>
                  <p className="text-muted-foreground text-lg mb-8">
                    Hỗ trợ các định dạng .xlsx, .xls, .csv
                  </p>
                  
                  <div className="flex justify-center gap-4">
                    <Button size="lg" variant={files.length > 0 ? "outline" : "default"} asChild className="text-base px-8 h-12">
                      <label className="cursor-pointer">
                        {files.length > 0 ? 'Chọn file khác' : 'Duyệt file...'}
                        <input type="file" multiple ref={fileInputRef} onChange={handleFileChange} accept=".csv, .xlsx, .xls" className="hidden" />
                      </label>
                    </Button>
                    
                    {files.length > 0 && (
                      <Button size="lg" onClick={handleProcess} disabled={loading} className="text-base px-8 h-12 bg-emerald-600 hover:bg-emerald-700">
                        {loading ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <Sparkles className="w-5 h-5 mr-2" />}
                        Bắt đầu xử lý
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
            {files.length > 0 && (
               <div className="mt-6 flex flex-col gap-2 max-w-md mx-auto">
                 {files.map(f => (
                   <div key={f.name} className="flex justify-between items-center text-sm p-3 bg-muted/50 rounded-lg border border-border">
                     <span className="font-medium truncate">{f.name}</span>
                     <span className="text-muted-foreground">{(f.size / 1024 / 1024).toFixed(2)} MB</span>
                   </div>
                 ))}
               </div>
            )}
          </CardContent>
        </Card>
        </motion.div>
      )}
      </AnimatePresence>

      {/* Step 3: Processing */}
      <AnimatePresence mode="wait">
      {currentStep === 3 && batchStatus && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
        >
        <Card className="border-0 shadow-2xl bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl relative overflow-hidden">
          {/* Animated background glow */}
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-blue-500/10 opacity-50 animate-pulse"></div>
          <CardContent className="p-12 text-center relative z-10">
            <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-8 relative">
              <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
              <Sparkles className="w-10 h-10 text-primary animate-pulse" />
            </div>
            
            <h3 className="text-2xl font-bold mb-4">AI đang làm việc...</h3>
            
            <div className="max-w-md mx-auto space-y-6">
              <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-primary h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${batchStatus.progress}%` }}
                ></div>
              </div>
              
              <div className="flex justify-between text-base font-medium">
                <span className="text-muted-foreground">{batchStatus.status_message}</span>
                <span className="text-primary">{batchStatus.progress}%</span>
              </div>
              
              <div className="text-sm text-muted-foreground/80 mt-2">
                (Đang xử lý file {batchStatus.completed_jobs + (batchStatus.current_job ? 1 : 0)} / {batchStatus.total_jobs})
              </div>

              <div className="pt-8">
                <Button variant="outline" onClick={handleCancelBatch} className="text-destructive hover:text-destructive">
                  Hủy tiến trình
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        </motion.div>
      )}
      </AnimatePresence>

      {/* Step 4: Done */}
      <AnimatePresence mode="wait">
      {currentStep === 4 && batchStatus && (
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
          className="space-y-6"
        >
          <Card className="border-0 bg-emerald-500/10 dark:bg-emerald-500/5 shadow-2xl backdrop-blur-xl relative overflow-hidden">
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl"></div>
            <CardContent className="p-10 text-center relative z-10">
              <div className="w-20 h-20 rounded-full bg-emerald-500 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-emerald-500/20">
                <CheckCircle className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-3xl font-bold text-emerald-700 mb-2">Hoàn Thành Tuyệt Vời!</h3>
              <p className="text-emerald-600/80 text-lg mb-8">
                Hệ thống đã làm sạch toàn bộ dữ liệu. Vui lòng tải file về để xem kết quả.
              </p>
              
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Button size="lg" asChild className="bg-emerald-600 hover:bg-emerald-700 text-base h-14 px-8 shadow-md">
                  <a href={`${API_URL}/api/batches/${activeBatchId}/download-merged?token=${localStorage.getItem('token')}`}>
                    <Download className="w-5 h-5 mr-2" />
                    Tải File Đã Gộp
                  </a>
                </Button>
                {batchStatus.total_jobs > 1 && (
                  <Button size="lg" variant="outline" asChild className="text-base h-14 px-8 bg-white">
                    <a href={`${API_URL}/api/batches/${activeBatchId}/download-zip?token=${localStorage.getItem('token')}`}>
                      <Download className="w-5 h-5 mr-2" />
                      Tải File ZIP (Từng file)
                    </a>
                  </Button>
                )}
                <Button size="lg" variant="secondary" onClick={resetPage} className="text-base h-14 px-8">
                  <RefreshCw className="w-5 h-5 mr-2" />
                  Làm Sạch File Khác
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-blue-50/50 border-blue-200">
            <CardContent className="p-6">
              <h4 className="font-bold text-blue-800 text-lg mb-3">💡 Hướng dẫn xem dữ liệu:</h4>
              <p className="text-blue-700/80 mb-4 text-base">File Excel bạn tải về đã được chia thành 3 Sheet để bạn dễ thao tác:</p>
              <ul className="space-y-3 text-base text-blue-800">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                  <span><strong>Sheet 1 (Dữ liệu chuẩn hóa):</strong> Các dòng đã được AI xử lý chính xác hoàn toàn. Bạn có thể dùng luôn.</span>
                </li>
                <li className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  <span><strong>Sheet 2 (Cần Nghiệp Vụ):</strong> Các dòng chứa sản phẩm chưa từng có trong quá khứ. Cần bạn tự gán "Dòng SP".</span>
                </li>
                <li className="flex items-start gap-2">
                  <Sparkles className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                  <span><strong>Sheet 3 (Gom nhóm Ngoại lệ):</strong> Tổng hợp những sản phẩm mới xuất hiện nhiều nhất để bạn ưu tiên xử lý trước.</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      )}
      </AnimatePresence>
    </div>
  );
};

export default CleanData;
