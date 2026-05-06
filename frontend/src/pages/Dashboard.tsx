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

const API_BASE = "http://localhost:8000";

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
      const response = await fetch(`${API_BASE}/api/jobs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) {
        if (response.status !== 401) throw new Error('Failed to fetch jobs');
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
        const response = await fetch(`${API_BASE}/api/jobs/${job.id}/preview?limit=50`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (response.ok) {
          const data = await response.json();
          setPreview(data.preview);
        }
      } catch (err) {
        // ignore preview error silently
      }
    }
  };

  const deleteJob = async (jobId: string) => {
    if (!window.confirm("Are you sure you want to delete this job and its file?")) return;
    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error("Delete failed");
      fetchJobs();
      if (selectedJob && selectedJob.id === jobId) setModalOpen(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const totalRows = jobs.reduce((acc, job) => acc + (job.total_rows || 0), 0);
  const completedJobs = jobs.filter(j => j.status === 'done').length;

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Overview of your data processing history
          </p>
        </div>
        <Button onClick={fetchJobs} variant="outline" size="sm" className="gap-2">
          <RefreshCw className={loading ? "animate-spin size-4" : "size-4"} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Files</CardTitle>
            <History className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
            <CheckCircle className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedJobs}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Rows Processed</CardTitle>
            <Database className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRows.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20 text-sm font-medium">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Processing History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.length > 0 ? (
                  jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium max-w-[200px] truncate">{job.filename}</TableCell>
                      <TableCell>
                        <Badge variant={job.status === 'done' ? 'default' : job.status === 'error' ? 'destructive' : 'secondary'}>
                          {job.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{job.total_rows ? `${job.total_rows}x${job.total_columns}` : '-'}</TableCell>
                      <TableCell>{job.processing_time_ms ? `${(job.processing_time_ms / 1000).toFixed(1)}s` : '-'}</TableCell>
                      <TableCell className="text-muted-foreground text-xs">{new Date(job.created_at).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="icon" onClick={() => openJobDetails(job)}>
                            <Eye className="size-4" />
                          </Button>
                          {job.status === 'done' && (
                            <Button variant="ghost" size="icon" asChild>
                              <a href={`${API_BASE}/api/jobs/${job.id}/download?token=${localStorage.getItem('token')}`}>
                                <Download className="size-4" />
                              </a>
                            </Button>
                          )}
                          <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => deleteJob(job.id)}>
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      {loading ? "Loading history..." : "No jobs found. Go to Clean Data to upload a file."}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
          <p className="mt-4 text-xs text-muted-foreground italic">
            Notice: We only retain your 10 most recent files. Older files are automatically deleted.
          </p>
        </CardContent>
      </Card>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Details: {selectedJob?.filename}</DialogTitle>
          </DialogHeader>
          
          {selectedJob && (
            <div className="flex-1 overflow-hidden flex flex-col gap-6 py-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm bg-muted/30 p-4 rounded-lg">
                <div>
                  <div className="text-muted-foreground">Status</div>
                  <div className="font-medium capitalize">{selectedJob.status}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Date</div>
                  <div className="font-medium">{new Date(selectedJob.created_at).toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Rows/Cols</div>
                  <div className="font-medium">{selectedJob.total_rows || '-'} / {selectedJob.total_columns || '-'}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Duration</div>
                  <div className="font-medium">{selectedJob.processing_time_ms ? (selectedJob.processing_time_ms/1000).toFixed(1) + 's' : '-'}</div>
                </div>
              </div>

              {selectedJob.error_message && (
                <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm border border-destructive/20 font-medium">
                  <strong>Error:</strong> {selectedJob.error_message}
                </div>
              )}

              {preview.length > 0 && (
                <div className="flex-1 overflow-auto border rounded-md">
                  <Table className="relative">
                    <TableHeader className="sticky top-0 bg-background z-10">
                      <TableRow>
                        {Object.keys(preview[0]).map(col => (
                          <TableHead key={col} className="whitespace-nowrap">{col}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.map((row, i) => (
                        <TableRow key={i}>
                          {Object.keys(row).map(col => (
                            <TableCell key={col} className="whitespace-nowrap max-w-[300px] truncate">{row[col]}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
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
