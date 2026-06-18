import React, { useState } from 'react';
import { Upload, CheckCircle, RefreshCw, FileText, Database, Download } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { AlertCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DirectDictionaryGenerator = ({ onComplete }: { onComplete: () => void }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [dictName, setDictName] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      setError('Please provide HQ files.');
      return;
    }

    setLoading(true);
    setError('');
    setPreviewData([]);

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/generate/hq-direct`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const data = await res.json();
      if (res.ok) {
        setPreviewData(data.data);
      } else {
        setError(data.detail || 'Failed to generate dictionary');
      }
    } catch (err) {
      setError('An error occurred during direct generation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!dictName) {
      setError('Please enter a dictionary name.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/generate/hq-direct/save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dictionary_name: dictName,
          data: previewData
        })
      });

      const data = await res.json();
      if (res.ok) {
        onComplete();
      } else {
        setError(data.detail || 'Failed to save dictionary');
      }
    } catch (err) {
      setError('An error occurred while saving.');
    } finally {
      setSaving(false);
    }
  };

  const reset = () => {
    setFiles([]);
    setPreviewData([]);
    setDictName('');
    setError('');
  };

  return (
    <Card className="shadow-xl border-t-4 border-t-green-500">
      <CardHeader className="border-b bg-muted/30">
        <CardTitle className="flex items-center gap-2">
          <Database className="text-green-500 size-6" />
          Direct Mode (1-Step HQ files)
        </CardTitle>
        <CardDescription>
          Skip clustering and LLM labeling by directly extracting keywords from labeled HQ data.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-8 space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {previewData.length === 0 ? (
          <form onSubmit={handleGenerate} className="space-y-6">
            <div className="border-2 border-dashed rounded-xl p-8 text-center transition-all border-green-500/50 bg-green-500/5">
              <Upload className="size-8 text-green-600 mx-auto mb-4" />
              <div className="space-y-2">
                <Button variant={files.length > 0 ? "outline" : "default"} size="sm" asChild>
                  <label className="cursor-pointer bg-green-600 hover:bg-green-700 text-white">
                    {files.length > 0 ? "Change HQ Files" : "Select HQ Files"}
                    <input type="file" multiple accept=".xlsx,.csv,.xls" className="hidden" onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setFiles(Array.from(e.target.files));
                        setError('');
                      }
                    }} />
                  </label>
                </Button>
                <p className="text-xs text-muted-foreground">{files.length > 0 ? `${files.length} files selected` : "Excel (.xlsx) or CSV"}</p>
              </div>
            </div>

            <Button type="submit" className="w-full h-12 gap-2 bg-green-600 hover:bg-green-700 text-white" disabled={loading || files.length === 0}>
              {loading ? <RefreshCw className="size-5 animate-spin" /> : <FileText className="size-5" />}
              {loading ? "Extracting Keywords..." : "Generate Dictionary Directly"}
            </Button>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="bg-green-500/10 text-green-700 p-4 rounded-md text-sm border border-green-500/20 flex items-center gap-2">
              <CheckCircle className="size-5 shrink-0" />
              <div>
                <strong className="block mb-1">Extracted {previewData.length} category groups!</strong>
                Review the keywords below, then save the dictionary.
              </div>
            </div>

            <div className="border rounded-md overflow-hidden max-h-64 overflow-y-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted/50 text-xs uppercase sticky top-0">
                  <tr>
                    <th className="px-4 py-2 font-medium">Lớp 1 / Ngành</th>
                    <th className="px-4 py-2 font-medium">Lớp 2 / Chi tiết</th>
                    <th className="px-4 py-2 font-medium">Keyword (Top)</th>
                    <th className="px-4 py-2 font-medium">Số SP</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {previewData.map((row, idx) => (
                    <tr key={idx} className="hover:bg-muted/30">
                      <td className="px-4 py-2">{row['Lớp 1']}</td>
                      <td className="px-4 py-2 text-muted-foreground">{row['Lớp 2'] || '-'}</td>
                      <td className="px-4 py-2 font-mono text-xs text-primary max-w-xs truncate" title={row.Keyword}>{row.Keyword}</td>
                      <td className="px-4 py-2 font-medium">{row['Số lượng SP']}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Dictionary Name (CSV)</label>
              <Input 
                placeholder="e.g. hq_taxonomy_2025" 
                value={dictName} 
                onChange={(e) => setDictName(e.target.value)} 
              />
            </div>

            <div className="flex gap-4">
              <Button type="button" variant="outline" onClick={reset} className="flex-1">Start Over</Button>
              <Button type="button" onClick={handleSave} className="flex-[2] gap-2 bg-green-600 hover:bg-green-700 text-white" disabled={saving || !dictName}>
                {saving ? <RefreshCw className="size-5 animate-spin" /> : <Download className="size-5" />}
                {saving ? "Saving..." : "Save Dictionary"}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DirectDictionaryGenerator;
