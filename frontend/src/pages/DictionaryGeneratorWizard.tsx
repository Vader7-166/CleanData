import React, { useState, useRef } from 'react';
import { Upload, FileDown, ArrowRight, CheckCircle, BrainCircuit, AlertCircle, Loader2, Sparkles, RefreshCw } from 'lucide-react';
import usePersistedState from '../hooks/usePersistedState';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { cn } from '../components/ui/utils';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DictionaryGeneratorWizard = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = usePersistedState('wizard_step', 1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Step 1 State
  const [rawFile, setRawFile] = useState<File | null>(null);
  const [persistedRawFileName, setPersistedRawFileName] = usePersistedState('wizard_raw_filename', '');
  const [useLlm, setUseLlm] = usePersistedState('wizard_use_llm', true);

  // Step 2 State
  const [reviewedDraftFile, setReviewedDraftFile] = useState<File | null>(null);
  const [persistedDraftFileName, setPersistedDraftFileName] = usePersistedState('wizard_draft_filename', '');
  const [dictName, setDictName] = usePersistedState('wizard_dict_name', '');

  const resetWizard = () => {
    setStep(1);
    setRawFile(null);
    setPersistedRawFileName('');
    setReviewedDraftFile(null);
    setPersistedDraftFileName('');
    setDictName('');
    setSuccess('');
    setError('');
  };

  const handleStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Step 1 started. File:", rawFile?.name);
    if (!rawFile) {
      setError('Please provide raw file.');
      return;
    }

    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', rawFile);

    try {
      const token = localStorage.getItem('token');
      console.log("Calling API Step 1...");
      const res = await fetch(`${API_URL}/api/dictionaries/generate/step1?use_llm=${useLlm}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      console.log("API Step 1 Response status:", res.status);
      if (res.ok) {
        console.log("Blobbing...");
        const blob = await res.blob();
        console.log("Blob received. Size:", blob.size);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const filename = res.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'draft_taxonomy.xlsx';
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        
        setSuccess('Draft generated! Please review the Excel file, then proceed to Step 2.');
        setStep(2);
      } else {
        const data = await res.json();
        console.error("Step 1 Failed data:", data);
        setError(data.detail || 'Step 1 failed');
      }
    } catch (err) {
      console.error("Step 1 Exception:", err);
      setError('An error occurred during Step 1.');
    } finally {
      setLoading(false);
    }
  };

  const handleStep2 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawFile || !reviewedDraftFile || !dictName) {
      setError('Please provide all required files and dictionary name.');
      return;
    }

    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('raw_file', rawFile);
    formData.append('draft_file', reviewedDraftFile);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/generate/step2?dictionary_name=${encodeURIComponent(dictName)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setSuccess('Dictionary generated and saved successfully!');
        if (onComplete) onComplete();
        // Reset wizard
        setTimeout(resetWizard, 3000);
      } else {
        console.error('Step 2 Error:', data);
        setError(data.detail || 'Step 2 failed');
      }
    } catch (err) {
      console.error('Step 2 Exception:', err);
      setError('An error occurred during Step 2.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-xl border-t-4 border-t-primary">
      <CardHeader className="border-b bg-muted/30">
        <div className="flex justify-between items-center">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit className="text-primary size-6" />
              Wizard: Generation Pipeline
            </CardTitle>
            <CardDescription>Follow the steps below to build your customized dictionary.</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={step === 1 ? "default" : "outline"} className={cn("size-8 rounded-full flex items-center justify-center p-0", step > 1 && "bg-green-500 hover:bg-green-600 border-none text-white")}>
              {step > 1 ? <CheckCircle className="size-5" /> : "1"}
            </Badge>
            <div className="w-8 h-px bg-border"></div>
            <Badge variant={step === 2 ? "default" : "outline"} className="size-8 rounded-full flex items-center justify-center p-0">2</Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-8 space-y-6">
        {error && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm border border-destructive/20 flex items-center gap-2">
            <AlertCircle className="size-4 shrink-0" />
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-500/10 text-green-600 p-3 rounded-md text-sm border border-green-500/20 flex items-center gap-2">
            <CheckCircle className="size-4 shrink-0" />
            {success}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleStep1} className="space-y-6">
            <div className="bg-primary/5 border-l-4 border-primary p-4 rounded-r-lg">
              <h4 className="font-bold text-primary mb-1">Step 1: Clustering & Draft</h4>
              <p className="text-sm text-muted-foreground">Upload your raw NK/XK file. Our AI will group similar items and use LLM to suggest meaningful category names.</p>
            </div>

            <div className="space-y-4">
              <div className={cn(
                "border-2 border-dashed rounded-xl p-8 text-center transition-all",
                rawFile ? "border-primary bg-primary/5" : "border-border"
              )}>
                <Upload className="size-8 text-primary mx-auto mb-4" />
                <div className="space-y-2">
                  {persistedRawFileName && !rawFile ? (
                    <p className="text-sm font-medium text-orange-600 italic">Previous session: {persistedRawFileName}</p>
                  ) : null}
                  <Button variant={rawFile ? "outline" : "default"} size="sm" asChild>
                    <label className="cursor-pointer">
                      {rawFile || persistedRawFileName ? "Change File" : "Select Raw Data"}
                      <input type="file" accept=".xlsx,.csv" className="hidden" onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) { setRawFile(f); setPersistedRawFileName(f.name); setError(''); }
                      }} />
                    </label>
                  </Button>
                  <p className="text-xs text-muted-foreground">{rawFile ? rawFile.name : "Excel (.xlsx) or CSV"}</p>
                </div>
              </div>

              <div 
                className="flex items-center gap-3 p-3 rounded-lg border bg-muted/20 cursor-pointer hover:bg-muted/40 transition-colors"
                onClick={() => setUseLlm(!useLlm)}
              >
                <div className={cn(
                  "size-5 rounded border-2 flex items-center justify-center transition-all",
                  useLlm ? "bg-primary border-primary text-white" : "border-muted-foreground"
                )}>
                  {useLlm && <CheckCircle className="size-4" />}
                </div>
                <div className="space-y-0.5">
                  <p className="text-sm font-medium leading-none">Enable AI Labeling</p>
                  <p className="text-xs text-muted-foreground font-light">Use Llama 3.1 to generate human-readable category names.</p>
                </div>
              </div>
            </div>

            <Button type="submit" className="w-full h-12 gap-2" disabled={loading || !rawFile}>
              {loading ? <RefreshCw className="size-5 animate-spin" /> : <Sparkles className="size-5" />}
              {loading ? "AI is processing..." : "Generate & Download Draft"}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleStep2} className="space-y-8">
            <div className="bg-green-500/5 border-l-4 border-green-500 p-4 rounded-r-lg">
              <h4 className="font-bold text-green-600 mb-1">Step 2: Review & Finalize</h4>
              <p className="text-sm text-muted-foreground">Upload your reviewed Excel draft (with corrected Lớp 2 names) to extract the final keywords.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               <div className={cn("border rounded-lg p-4 space-y-3", rawFile ? "bg-muted/10 border-green-500/30" : "border-destructive/30 bg-destructive/5")}>
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Raw Data</h5>
                    {rawFile && <CheckCircle className="size-4 text-green-500" />}
                  </div>
                  <p className="text-sm font-medium truncate">{rawFile ? rawFile.name : persistedRawFileName || "Missing File"}</p>
                  <Button variant="outline" size="sm" className="w-full text-[10px] h-7" asChild>
                    <label className="cursor-pointer">
                      Relink File
                      <input type="file" accept=".xlsx,.csv" className="hidden" onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) { setRawFile(f); setPersistedRawFileName(f.name); }
                      }} />
                    </label>
                  </Button>
               </div>

               <div className={cn("border rounded-lg p-4 space-y-3", reviewedDraftFile ? "bg-muted/10 border-green-500/30" : "border-primary/30 bg-primary/5")}>
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Reviewed Draft</h5>
                    {reviewedDraftFile && <CheckCircle className="size-4 text-green-500" />}
                  </div>
                  <p className="text-sm font-medium truncate">{reviewedDraftFile ? reviewedDraftFile.name : persistedDraftFileName || "Select Excel file"}</p>
                  <Button variant={reviewedDraftFile ? "outline" : "default"} size="sm" className="w-full text-[10px] h-7" asChild>
                    <label className="cursor-pointer">
                      {reviewedDraftFile ? "Change Draft" : "Select Draft"}
                      <input type="file" accept=".xlsx" className="hidden" onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) { setReviewedDraftFile(f); setPersistedDraftFileName(f.name); }
                      }} />
                    </label>
                  </Button>
               </div>
            </div>

            <div className="space-y-2 text-left">
              <label className="text-sm font-medium">Final Dictionary Name</label>
              <Input 
                placeholder="e.g. glassware_taxonomy_v1" 
                value={dictName} 
                onChange={(e) => setDictName(e.target.value)} 
              />
            </div>

            <div className="flex gap-4 pt-2">
              <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1">Back</Button>
              <Button type="submit" className="flex-[2] gap-2 bg-green-600 hover:bg-green-700 text-white" disabled={loading || !rawFile || !reviewedDraftFile || !dictName}>
                {loading ? <RefreshCw className="size-5 animate-spin" /> : <CheckCircle className="size-5" />}
                {loading ? "Extracting..." : "Finalize & Save"}
              </Button>
            </div>
          </form>
        )}
      </CardContent>

      <CardFooter className="border-t bg-muted/20 flex justify-center py-4">
        <button type="button" onClick={resetWizard} className="text-xs text-muted-foreground hover:text-destructive underline transition-colors">
          Reset Pipeline & Clear Cached Files
        </button>
      </CardFooter>
    </Card>
  );
};

export default DictionaryGeneratorWizard;
