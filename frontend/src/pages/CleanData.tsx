import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Download, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import usePersistedState from '../hooks/usePersistedState';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CleanData = () => {
  const [file, setFile] = useState<File | null>(null);
  const [persistedFileName, setPersistedFileName] = usePersistedState('clean_data_filename', '');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = usePersistedState<string[]>('clean_data_logs', []);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ jobId: string; preview: any[] } | null>(null);
  const [activeJobId, setActiveJobId] = usePersistedState<string | null>('clean_data_job_id', null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resume job if found on mount
  useEffect(() => {
    if (activeJobId && !result && !loading) {
      resumeJob(activeJobId);
    }
  }, []);

  const resumeJob = async (jobId: string) => {
    setLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/preview`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setResult({ jobId, preview: data.preview });
        setLoading(false);
      } else {
        connectToStream(jobId, token!);
      }
    } catch (err) {
      console.error("Error resuming job:", err);
      resetPage();
    }
  };

  const connectToStream = (jobId: string, token: string) => {
    const evtSource = new EventSource(`${API_URL}/stream/${jobId}?token=${token}`);
      
    evtSource.onmessage = async (e) => {
      const eventData = JSON.parse(e.data);
      if (eventData.event === 'progress') {
        setLogs((prev: string[]) => [...prev, eventData.data]);
      } else if (eventData.event === 'done') {
        evtSource.close();
        await fetchResults(jobId);
      } else if (eventData.event === 'error') {
        evtSource.close();
        setError(eventData.data);
        setLoading(false);
        setActiveJobId(null);
      }
    };

    evtSource.onerror = () => {
      evtSource.close();
      fetchResults(jobId).catch(() => {
        setError("Connection to progress stream lost.");
        setLoading(false);
      });
    };
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPersistedFileName(selectedFile.name);
      setError('');
      setResult(null);
      setLogs([]);
    }
  };

  const handleProcess = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setLogs([]);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

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
      const jobId = data.job_id;
      setActiveJobId(jobId);

      connectToStream(jobId, token!);

    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchResults = async (jobId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}/preview`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error("Failed to load preview.");
      const data = await response.json();
      setResult({ jobId, preview: data.preview });
    } catch(err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetPage = () => {
    setFile(null);
    setPersistedFileName('');
    setResult(null);
    setLogs([]);
    setError('');
    setActiveJobId(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Clean Data</h2>
        <p className="text-muted-foreground">
          Upload an Excel or CSV file to sanitize and predict missing columns using AI.
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20 flex items-center gap-3">
          <AlertCircle className="size-5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {!result && !loading && (
        <Card className="max-w-3xl mx-auto">
          <CardContent className="pt-6">
            <div 
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                file ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <UploadCloud className="w-8 h-8 text-primary" />
                </div>
                <div>
                  {persistedFileName && !file ? (
                    <div className="space-y-2">
                      <p className="font-semibold text-primary">Previous session found: {persistedFileName}</p>
                      <p className="text-sm text-muted-foreground">Please re-select this file to continue or start over.</p>
                    </div>
                  ) : (
                    <p className="mb-2 font-medium text-lg">
                      {file ? file.name : "Kéo thả tệp Excel vào đây"}
                    </p>
                  )}
                  
                  <div className="mt-4 flex flex-col items-center gap-4">
                    <Button variant={file ? "outline" : "default"} asChild>
                      <label className="cursor-pointer">
                        {file || persistedFileName ? 'Change File' : 'Browse File'}
                        <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".csv, .xlsx, .xls" className="hidden" />
                      </label>
                    </Button>
                    <p className="text-xs text-muted-foreground">
                      Hỗ trợ định dạng: .xlsx, .xls, .csv
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-center">
              <Button 
                onClick={handleProcess} 
                disabled={!file} 
                className="w-full max-w-sm h-12 text-lg font-semibold"
              >
                {file ? "Start Processing" : "Select a file to begin"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card className="max-w-3xl mx-auto">
          <CardContent className="pt-12 pb-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="size-20 border-4 border-primary/20 rounded-full animate-pulse"></div>
                <RefreshCw className="size-10 text-primary animate-spin absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold">Processing Data...</h3>
              <p className="text-muted-foreground">Using Hybrid NLP Model for prediction</p>
            </div>
            
            <div className="text-left bg-muted/50 rounded-lg p-6 font-mono text-sm max-h-[300px] overflow-y-auto border">
              {logs.length > 0 ? (
                <ul className="space-y-1">
                  {logs.map((log, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-primary/50">[{new Date().toLocaleTimeString()}]</span>
                      <span>{log}</span>
                    </li>
                  ))}
                  <div className="animate-pulse inline-block w-2 h-4 bg-primary/50 ml-1 translate-y-1"></div>
                </ul>
              ) : (
                <p className="text-muted-foreground italic">Waiting for logs...</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {result && (
        <div className="space-y-6">
          <Card className="border-green-500/20 bg-green-500/5">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-600">
                  <CheckCircle className="size-6" />
                </div>
                <div>
                  <CardTitle className="text-green-700">Success!</CardTitle>
                  <CardDescription className="text-green-600/80">Your dataset has been successfully processed.</CardDescription>
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="default" className="bg-green-600 hover:bg-green-700" asChild>
                  <a href={`${API_URL}/api/jobs/${result.jobId}/download?token=${localStorage.getItem('token')}`}>
                    <Download className="size-4 mr-2" />
                    Download Result
                  </a>
                </Button>
                <Button variant="outline" onClick={resetPage}>Process Another</Button>
              </div>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Data Preview</CardTitle>
              <CardDescription>Showing first few rows of the cleaned data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border overflow-hidden">
                <div className="overflow-x-auto max-h-[500px]">
                  <Table className="relative">
                    <TableHeader className="sticky top-0 bg-background z-10 border-b">
                      <TableRow>
                        {result.preview.length > 0 && Object.keys(result.preview[0]).map(col => (
                          <TableHead key={col} className="whitespace-nowrap">{col}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.preview.map((row, i) => (
                        <TableRow key={i}>
                          {Object.keys(row).map(col => (
                            <TableCell key={col} className="whitespace-nowrap max-w-[300px] truncate">{row[col]}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CleanData;
