import React, { useState, useEffect } from 'react';
import { Download, Trash2, CheckCircle, Upload, BookOpen, AlertCircle, Calendar, Activity } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DictionaryItem {
  id: string;
  filename: string;
  is_active: boolean;
  created_at: string;
}

const Dictionary = () => {
  const [dictionaries, setDictionaries] = useState<DictionaryItem[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const fetchDictionaries = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setDictionaries(data.dictionaries);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        const statsMap: Record<string, number> = {};
        data.stats.forEach((s: any) => {
          statsMap[s.dictionary_id] = s.usage_count;
        });
        setStats(statsMap);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownload = async (id: string, filename: string) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/${id}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      console.error('Download failed', err);
    }
  };

  useEffect(() => {
    fetchDictionaries();
    fetchStats();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setFile(null);
        fetchDictionaries();
      } else {
        const errorDetail = data.detail;
        if (typeof errorDetail === 'string') {
          setError(errorDetail);
        } else if (Array.isArray(errorDetail)) {
          setError(errorDetail[0]?.msg || 'Upload failed');
        } else {
          setError('Upload failed');
        }
      }
    } catch (err) {
      setError('An error occurred during upload.');
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (id: string) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/${id}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchDictionaries();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this dictionary?")) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchDictionaries();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dictionary Management</h2>
        <p className="text-muted-foreground">
          Manage your custom dictionaries and view usage statistics.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload New Dictionary</CardTitle>
          <CardDescription>Supported format: CSV (must follow the taxonomy structure)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Select CSV File</label>
              <Input 
                type="file" 
                accept=".csv" 
                onChange={handleFileChange}
                className="cursor-pointer"
              />
            </div>
            <Button 
              onClick={handleUpload} 
              disabled={!file || uploading} 
              className="gap-2 min-w-[140px]"
            >
              {uploading ? <RefreshCw className="size-4 animate-spin" /> : <Upload className="size-4" />}
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </div>
          {error && (
            <div className="mt-4 bg-destructive/10 text-destructive p-3 rounded-md text-sm flex items-center gap-2 border border-destructive/20">
              <AlertCircle className="size-4" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h3 className="text-xl font-bold">Available Dictionaries</h3>
        
        {dictionaries.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-muted-foreground">
              <div className="flex flex-col items-center gap-2">
                <BookOpen className="size-8 opacity-20" />
                <p>No dictionaries uploaded yet.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dictionaries.map(dict => (
              <Card key={dict.id} className={dict.is_active ? "border-primary ring-1 ring-primary/20" : ""}>
                <CardContent className="p-6">
                  <div className="flex flex-col h-full gap-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold truncate max-w-[200px]" title={dict.filename}>{dict.filename}</h4>
                          {dict.is_active && <Badge className="bg-primary hover:bg-primary">Active</Badge>}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><Calendar className="size-3" /> {new Date(dict.created_at).toLocaleDateString()}</span>
                          <span className="flex items-center gap-1"><Activity className="size-3" /> {stats[dict.id] || 0} uses</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="icon" className="size-8" onClick={() => handleDownload(dict.id, dict.filename)} title="Download">
                          <Download className="size-4" />
                        </Button>
                        <Button variant="outline" size="icon" className="size-8 text-destructive hover:bg-destructive/10" onClick={() => handleDelete(dict.id)} title="Delete">
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {!dict.is_active && (
                      <Button 
                        variant="secondary" 
                        size="sm" 
                        className="w-full gap-2 mt-2"
                        onClick={() => handleActivate(dict.id)}
                      >
                        <CheckCircle className="size-4" />
                        Set as Active
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dictionary;
