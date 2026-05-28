import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Download, RefreshCw, CheckCircle, AlertCircle, FileText, Check, Clock, PlayCircle } from 'lucide-react';
import usePersistedState from '../hooks/usePersistedState';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import BatchPreviewDialog from '../components/BatchPreviewDialog';
import { useFileContext } from '../contexts/FileContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CleanData = () => {
  const { cleanDataFiles: files, setCleanDataFiles: setFiles } = useFileContext();
  const [transactionTypes, setTransactionTypes] = useState<Record<string, string>>({});
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
          
          if (data.status === 'done' || data.status === 'error') {
            stopPolling();
            setLoading(false);
          }
        } else {
          stopPolling();
          setError("Failed to fetch batch status.");
          setLoading(false);
        }
      } catch (err) {
        stopPolling();
        setError("Network error fetching batch status.");
        setLoading(false);
      }
    }, 2000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(selectedFiles);
      
      const newTypes: Record<string, string> = {};
      selectedFiles.forEach(f => {
        newTypes[f.name] = ""; // default to auto
      });
      setTransactionTypes(newTypes);
      setError('');
    }
  };

  const handleTypeChange = (filename: string, type: string) => {
    setTransactionTypes(prev => ({ ...prev, [filename]: type === "auto" ? "" : type }));
  };

  const handleProcess = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('transaction_types', JSON.stringify(transactionTypes));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await response.json();
      setActiveBatchId(data.batch_id);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const resetPage = () => {
    setFiles([]);
    setTransactionTypes({});
    setBatchStatus(null);
    setError('');
    setActiveBatchId(null);
    stopPolling();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Batch Clean Data</h2>
        <p className="text-muted-foreground">
          Upload multiple Excel/CSV files for batch processing. Dictionaries are automatically routed by HS code.
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20 flex items-center gap-3">
          <AlertCircle className="size-5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Upload Phase */}
      {!batchStatus && !loading && (
        <Card className="max-w-3xl mx-auto">
          <CardContent className="pt-6">
            <div 
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                files.length > 0 ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <UploadCloud className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <p className="mb-2 font-medium text-lg">
                    {files.length > 0 ? `${files.length} files selected` : "Drag and drop files here"}
                  </p>
                  
                  <div className="mt-4 flex flex-col items-center gap-4">
                    <Button variant={files.length > 0 ? "outline" : "default"} asChild>
                      <label className="cursor-pointer">
                        {files.length > 0 ? 'Change Files' : 'Browse Files'}
                        <input type="file" multiple ref={fileInputRef} onChange={handleFileChange} accept=".csv, .xlsx, .xls" className="hidden" />
                      </label>
                    </Button>
                    <p className="text-xs text-muted-foreground">
                      Supported formats: .xlsx, .xls, .csv
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {files.length > 0 && (
              <div className="mt-8 space-y-4">
                <h4 className="font-semibold text-sm">File Configuration</h4>
                <div className="space-y-3">
                  {files.map(f => (
                    <div key={f.name} className="flex items-center justify-between bg-muted/50 p-3 rounded-lg border">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <FileText className="text-primary/70 shrink-0" size={18} />
                        <span className="text-sm font-medium truncate">{f.name}</span>
                      </div>
                      <div className="w-48 shrink-0">
                        <Select value={transactionTypes[f.name] || "auto"} onValueChange={(val) => handleTypeChange(f.name, val)}>
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue placeholder="Loại giao dịch" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="auto">Tự động (Auto)</SelectItem>
                            <SelectItem value="Nhập khẩu">Nhập khẩu</SelectItem>
                            <SelectItem value="Xuất khẩu">Xuất khẩu</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-4 flex justify-center">
                  <Button onClick={handleProcess} className="w-full max-w-sm h-12 text-lg font-semibold">
                    <PlayCircle className="mr-2" /> Start Batch Processing
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Processing / Done Phase */}
      {(batchStatus || loading) && (
        <div className="space-y-6">
          <Card className="max-w-3xl mx-auto">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle>Batch Processing Queue</CardTitle>
                <CardDescription>Files are being processed sequentially</CardDescription>
              </div>
              {batchStatus?.status === 'done' && (
                <Badge className="bg-green-500 hover:bg-green-600">Completed</Badge>
              )}
              {(!batchStatus || batchStatus?.status === 'processing') && (
                <Badge variant="outline" className="text-blue-500 border-blue-500/30 bg-blue-500/10">Processing...</Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {!batchStatus ? (
                <div className="py-8 flex justify-center"><RefreshCw className="animate-spin text-primary" /></div>
              ) : (
                <div className="space-y-3">
                  {batchStatus.jobs.map((job: any) => (
                    <div key={job.id} className="flex items-center justify-between p-4 rounded-lg border bg-card">
                      <div className="flex items-center gap-4">
                        {job.status === 'done' ? (
                          <div className="rounded-full p-1.5 bg-green-500/20 text-green-600"><Check size={16} /></div>
                        ) : job.status === 'processing' ? (
                          <div className="rounded-full p-1.5 bg-blue-500/20 text-blue-600"><RefreshCw size={16} className="animate-spin" /></div>
                        ) : job.status === 'error' ? (
                          <div className="rounded-full p-1.5 bg-red-500/20 text-red-600"><AlertCircle size={16} /></div>
                        ) : (
                          <div className="rounded-full p-1.5 bg-muted text-muted-foreground"><Clock size={16} /></div>
                        )}
                        <div>
                          <p className="font-medium text-sm">{job.filename}</p>
                          {job.error_message ? (
                            <p className="text-xs text-red-500 mt-0.5">{job.error_message}</p>
                          ) : (
                            <p className="text-xs text-muted-foreground mt-0.5 capitalize">
                              {job.status} • {job.transaction_type || 'Auto-detected'}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      {job.status === 'done' && (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={`${API_URL}/api/jobs/${job.id}/download?token=${localStorage.getItem('token')}`}>
                            <Download className="mr-2 size-4" /> Download
                          </a>
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {batchStatus?.status === 'done' && (
            <Card className="max-w-3xl mx-auto border-green-500/20 bg-green-500/5">
              <CardContent className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="size-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-600">
                    <CheckCircle className="size-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-green-700">Batch Complete</h3>
                    <p className="text-sm text-green-600/80">All files have been processed and sanitized.</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <BatchPreviewDialog batchId={batchStatus.id} />
                  <Button variant="outline" onClick={resetPage}>New Batch</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default CleanData;
