import React, { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Download, Eye, History, CheckCircle, Database } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Job {
  id: string;
  filename: string;
  status: string;
  total_rows?: number;
  total_columns?: number;
  processing_time_ms?: number;
  created_at: string;
  error_message?: string;
}

const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Modal states
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [preview, setPreview] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/jobs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) {
        if (response.status !== 401) throw new Error('Lỗi khi tải dữ liệu');
      } else {
        const data = await response.json();
        setJobs(data.jobs);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const openJobDetails = async (job: Job) => {
    setSelectedJob(job);
    setPreview([]);
    setModalOpen(true);
    
    if (job.status === 'done') {
      try {
        const response = await fetch(`${API_URL}/api/jobs/${job.id}/preview?limit=50`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (response.ok) {
          const data = await response.json();
          setPreview(data.preview);
        }
      } catch (err) {
        // ignore
      }
    }
  };

  const deleteJob = async (jobId: string) => {
    if (!window.confirm("Bạn có chắc muốn xóa file này?")) return;
    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error("Xóa thất bại");
      fetchJobs();
      if (selectedJob && selectedJob.id === jobId) setModalOpen(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const totalRows = jobs.reduce((acc, job) => acc + (job.total_rows || 0), 0);
  const completedJobs = jobs.filter(j => j.status === 'done').length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Tổng Quan</h2>
          <p className="text-muted-foreground">Theo dõi lịch sử làm sạch dữ liệu và thống kê.</p>
        </div>
        <Button onClick={fetchJobs} disabled={loading} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-primary/20 rounded-lg text-primary">
              <History className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Tổng số tác vụ</p>
              <h3 className="text-3xl font-bold">{jobs.length}</h3>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-emerald-500/5 to-emerald-500/10 border-emerald-500/20">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/20 rounded-lg text-emerald-600">
              <CheckCircle className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Tác vụ hoàn thành</p>
              <h3 className="text-3xl font-bold">{completedJobs}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/5 to-blue-500/10 border-blue-500/20">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-blue-500/20 rounded-lg text-blue-600">
              <Database className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Tổng số dòng đã xử lý</p>
              <h3 className="text-3xl font-bold">{totalRows.toLocaleString()}</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lịch Sử Tác Vụ</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="text-destructive mb-4">{error}</p>}
          
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên File</TableHead>
                  <TableHead>Trạng Thái</TableHead>
                  <TableHead className="text-right">Số Dòng</TableHead>
                  <TableHead className="text-right">Thời Gian (ms)</TableHead>
                  <TableHead>Ngày Tạo</TableHead>
                  <TableHead className="text-right">Thao Tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center h-24 text-muted-foreground">
                      Chưa có tác vụ nào. Hãy vào màn hình Làm Sạch Dữ Liệu để tải file lên.
                    </TableCell>
                  </TableRow>
                ) : (
                  jobs.map(job => (
                    <TableRow key={job.id} className="cursor-pointer hover:bg-muted/50" onClick={() => openJobDetails(job)}>
                      <TableCell className="font-medium max-w-[200px] truncate" title={job.filename}>
                        {job.filename}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={job.status === 'done' ? 'default' : job.status === 'error' ? 'destructive' : 'secondary'}
                          className={job.status === 'done' ? 'bg-emerald-500' : ''}
                        >
                          {job.status === 'done' ? 'Hoàn thành' : job.status === 'error' ? 'Lỗi' : 'Đang chờ'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{job.total_rows?.toLocaleString() || '-'}</TableCell>
                      <TableCell className="text-right">{job.processing_time_ms || '-'}</TableCell>
                      <TableCell>{new Date(job.created_at).toLocaleString('vi-VN')}</TableCell>
                      <TableCell className="text-right space-x-2" onClick={e => e.stopPropagation()}>
                        {job.status === 'done' && (
                          <Button size="icon" variant="ghost" asChild title="Tải xuống">
                            <a href={`${API_URL}/api/jobs/${job.id}/download?token=${localStorage.getItem('token')}`}>
                              <Download className="w-4 h-4" />
                            </a>
                          </Button>
                        )}
                        <Button size="icon" variant="ghost" className="text-destructive hover:text-destructive" onClick={() => deleteJob(job.id)} title="Xóa">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Chi Tiết Tác Vụ</DialogTitle>
          </DialogHeader>
          {selectedJob && (
            <div className="space-y-6 pt-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">ID</p>
                  <p className="text-sm font-mono">{selectedJob.id.slice(0,8)}...</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Tên File</p>
                  <p className="text-sm truncate" title={selectedJob.filename}>{selectedJob.filename}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Trạng Thái</p>
                  <Badge variant={selectedJob.status === 'done' ? 'default' : 'secondary'}>
                    {selectedJob.status === 'done' ? 'Hoàn thành' : selectedJob.status}
                  </Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Tổng Số Dòng</p>
                  <p className="text-sm">{selectedJob.total_rows || 0}</p>
                </div>
              </div>

              {selectedJob.status === 'error' && (
                <div className="bg-destructive/10 text-destructive p-4 rounded-md border border-destructive/20 text-sm">
                  {selectedJob.error_message}
                </div>
              )}

              {selectedJob.status === 'done' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium flex items-center gap-2">
                      <Eye className="w-4 h-4 text-muted-foreground" />
                      Xem Trước Dữ Liệu (50 dòng đầu)
                    </h4>
                    <Button size="sm" asChild>
                      <a href={`${API_URL}/api/jobs/${selectedJob.id}/download?token=${localStorage.getItem('token')}`} className="gap-2">
                        <Download className="w-4 h-4" />
                        Tải Xuống
                      </a>
                    </Button>
                  </div>
                  
                  {preview.length > 0 ? (
                    <div className="rounded-md border overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {Object.keys(preview[0]).map(k => (
                              <TableHead key={k} className="whitespace-nowrap">{k}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {preview.map((row, idx) => (
                            <TableRow key={idx}>
                              {Object.values(row).map((val: any, vidx) => (
                                <TableCell key={vidx} className="whitespace-nowrap max-w-[200px] truncate" title={String(val || '')}>
                                  {val || '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="p-8 text-center text-muted-foreground border rounded-md bg-muted/20">
                      Không thể lấy dữ liệu xem trước
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
