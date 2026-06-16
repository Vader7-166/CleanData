import React, { useState, useRef, useEffect } from 'react';
import { Upload, CheckCircle, BrainCircuit, AlertCircle, Sparkles, RefreshCw, Database } from 'lucide-react';
import usePersistedState from '../hooks/usePersistedState';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { cn } from '../components/ui/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useFileContext } from '../contexts/FileContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DictionaryGeneratorWizard = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = usePersistedState('wizard_step', 1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Step 1 State
  const { dictionaryRawFiles: rawFiles, setDictionaryRawFiles: setRawFiles, dictionaryDraftFile: reviewedDraftFile, setDictionaryDraftFile: setReviewedDraftFile } = useFileContext();
  const [persistedRawFileName, setPersistedRawFileName] = usePersistedState('wizard_raw_filename', '');
  const [useLlm, setUseLlm] = usePersistedState('wizard_use_llm', true);
  const [jobId, setJobId] = usePersistedState('wizard_job_id', '');
  const [jobProgress, setJobProgress] = useState<{current: number, total: number, message: string} | null>(null);

  // Step 2 State
  const [persistedDraftFileName, setPersistedDraftFileName] = usePersistedState('wizard_draft_filename', '');
  const [dictName, setDictName] = usePersistedState('wizard_dict_name', '');
  // HS Code interception state
  const [hsCheckOpen, setHsCheckOpen] = useState(false);
  const [unresolvedHsCodes, setUnresolvedHsCodes] = useState<{hs_code: string; dong_sp: string; industry_name: string; default_type: string}[]>([]);
  const [hsCheckLoading, setHsCheckLoading] = useState(false);
  const pendingStep1Ref = useRef(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (jobId && step === 1) {
      setLoading(true);
      interval = setInterval(async () => {
        try {
          const token = localStorage.getItem('token');
          const res = await fetch(`${API_URL}/api/dictionaries/generate/status/${jobId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setJobProgress(data.progress);
            if (data.status === 'done') {
              clearInterval(interval);
              setLoading(false);
              setJobId('');
              
              const dlRes = await fetch(`${API_URL}/api/dictionaries/generate/download/${jobId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
              });
              if (dlRes.ok) {
                const blob = await dlRes.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `draft_taxonomy_${jobId.substring(0,8)}.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                
                setSuccess('Draft generated! Please review the Excel file, then proceed to Step 2.');
                setStep(2);
              } else {
                setError('Failed to download generated draft.');
              }
            } else if (data.status === 'error') {
              clearInterval(interval);
              setLoading(false);
              setJobId('');
              setError(`Generation failed: ${data.error_message}`);
            }
          } else {
             if (res.status === 404) {
               clearInterval(interval);
               setLoading(false);
               setJobId('');
             }
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobId, step]);

  const DONG_SP_OPTIONS = [
    'SP BÌNH/PHÍCH', 'SP THỦY TINH', 'SP ĐÈN/BÓNG ĐÈN',
    'SP ĐÈN/THIẾT BỊ CHIẾU SÁNG', 'SP THIẾT BỊ ĐIỆN GIA DỤNG',
  ];

  const resetWizard = () => {
    setStep(1);
    setRawFiles([]);
    setPersistedRawFileName('');
    setReviewedDraftFile(null);
    setPersistedDraftFileName('');
    setDictName('');
    setJobId('');
    setJobProgress(null);
    setSuccess('');
    setError('');
  };

  const extractHsCodesFromFile = async (file: File): Promise<string[]> => {
    // Read the file and extract unique HS_Code values
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const text = event.target?.result as string;
          if (!text) { resolve([]); return; }
          const lines = text.split('\n');
          // Find HS_Code column index
          const headerLine = lines.find(l => l.includes('HS_Code'));
          if (!headerLine) { resolve([]); return; }
          const headers = headerLine.split(',').map(h => h.trim().replace(/"/g, ''));
          const hsIdx = headers.indexOf('HS_Code');
          if (hsIdx === -1) { resolve([]); return; }
          const codes = new Set<string>();
          for (let i = lines.indexOf(headerLine) + 1; i < lines.length; i++) {
            const cols = lines[i].split(',');
            if (cols[hsIdx]) {
              const code = cols[hsIdx].trim().replace(/"/g, '').replace(/\./g, '').replace(/\D/g, '');
              if (code.length >= 4) codes.add(code);
            }
          }
          resolve(Array.from(codes));
        } catch {
          resolve([]);
        }
      };
      // Only read CSV files for HS code extraction
      if (file.name.endsWith('.csv')) {
        reader.readAsText(file);
      } else {
        // For Excel files, skip pre-check and let the backend handle it
        resolve([]);
      }
    });
  };

  const proceedWithStep1 = async () => {
    if (rawFiles.length === 0) return;
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    rawFiles.forEach(file => formData.append('files', file));

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/dictionaries/generate/step1?use_llm=${useLlm}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setJobId(data.job_id);
        // Polling effect handles the rest
      } else {
        const data = await res.json();
        const errorDetail = data.detail;
        if (typeof errorDetail === 'string') setError(errorDetail);
        else if (Array.isArray(errorDetail)) setError(errorDetail[0]?.msg || 'Action failed');
        else setError('Action failed');
        setLoading(false);
      }
    } catch (err) {
      setError('An error occurred during Step 1.');
      setLoading(false);
    }
  };

  const handleStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rawFiles.length === 0) {
      setError('Please provide raw file.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Extract HS codes from raw files and check against DB
      let allHsCodes: string[] = [];
      for (const file of rawFiles) {
          const codes = await extractHsCodesFromFile(file);
          allHsCodes = [...allHsCodes, ...codes];
      }
      const hsCodes = Array.from(new Set(allHsCodes));
      
      if (hsCodes.length > 0) {
        const token = localStorage.getItem('token');
        const checkRes = await fetch(`${API_URL}/api/taxonomy/check-hs-codes`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ hs_codes: hsCodes }),
        });

        if (checkRes.ok) {
          const checkData = await checkRes.json();
          if (checkData.unresolved && checkData.unresolved.length > 0) {
            // Show interception dialog
            setUnresolvedHsCodes(
              checkData.unresolved.map((u: {hs_code: string}) => ({
                hs_code: u.hs_code,
                dong_sp: 'SP BÌNH/PHÍCH',
                industry_name: '',
                default_type: 'NC',
              }))
            );
            setHsCheckOpen(true);
            setLoading(false);
            return;
          }
        }
      }

      // No unresolved codes, proceed directly
      await proceedWithStep1();
    } catch (err) {
      setError('An error occurred during HS code validation.');
      setLoading(false);
    }
  };

  const handleSaveUnresolvedHsCodes = async () => {
    setHsCheckLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/taxonomy/bulk-save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: unresolvedHsCodes.map(u => ({
            hs_code_prefix: u.hs_code,
            dong_sp: u.dong_sp,
            industry_name: u.industry_name,
            default_type: u.default_type,
          })),
        }),
      });

      if (res.ok) {
        setHsCheckOpen(false);
        setUnresolvedHsCodes([]);
        // Proceed with Step 1 after saving
        await proceedWithStep1();
      } else {
        const data = await res.json();
        setError(data.detail || 'Failed to save HS codes.');
      }
    } catch {
      setError('Error saving HS taxonomy data.');
    } finally {
      setHsCheckLoading(false);
    }
  };

  const handleStep2 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rawFiles.length === 0 || !reviewedDraftFile || !dictName) {
      setError('Please provide all required files and dictionary name.');
      return;
    }

    setLoading(true);
    setError('');
    
    const formData = new FormData();
    rawFiles.forEach(file => formData.append('raw_files', file));
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
        const errorDetail = data.detail;
        if (typeof errorDetail === 'string') {
          setError(errorDetail);
        } else if (Array.isArray(errorDetail)) {
          setError(errorDetail[0]?.msg || 'Step 2 failed');
        } else {
          setError('Step 2 failed');
        }
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
                rawFiles.length > 0 ? "border-primary bg-primary/5" : "border-border"
              )}>
                <Upload className="size-8 text-primary mx-auto mb-4" />
                <div className="space-y-2">
                  {persistedRawFileName && rawFiles.length === 0 ? (
                    <p className="text-sm font-medium text-orange-600 italic">Previous session: {persistedRawFileName}</p>
                  ) : null}
                  <Button variant={rawFiles.length > 0 ? "outline" : "default"} size="sm" asChild>
                    <label className="cursor-pointer">
                      {rawFiles.length > 0 || persistedRawFileName ? "Change Files" : "Select Raw Data"}
                      <input type="file" multiple accept=".xlsx,.csv,.xls" className="hidden" onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          const fArray = Array.from(e.target.files);
                          setRawFiles(fArray); 
                          setPersistedRawFileName(fArray.map(f => f.name).join(', ')); 
                          setError(''); 
                        }
                      }} />
                    </label>
                  </Button>
                  <p className="text-xs text-muted-foreground">{rawFiles.length > 0 ? `${rawFiles.length} files selected` : "Excel (.xlsx) or CSV"}</p>
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

            <Button type="submit" className="w-full h-12 gap-2" disabled={loading || rawFiles.length === 0}>
              {loading ? <RefreshCw className="size-5 animate-spin" /> : <Sparkles className="size-5" />}
              {loading ? "AI is processing..." : "Generate AI Draft"}
            </Button>
            
            {loading && jobProgress && (
              <div className="mt-4 space-y-2">
                <div className="text-sm font-medium text-center">{jobProgress.message}</div>
                {jobProgress.total > 0 && (
                  <div className="w-full bg-secondary rounded-full h-2.5">
                    <div 
                      className="bg-primary h-2.5 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, Math.max(0, (jobProgress.current / jobProgress.total) * 100))}%` }}
                    ></div>
                  </div>
                )}
              </div>
            )}
          </form>
        ) : (
          <form onSubmit={handleStep2} className="space-y-8">
            <div className="bg-green-500/5 border-l-4 border-green-500 p-4 rounded-r-lg">
              <h4 className="font-bold text-green-600 mb-1">Step 2: Review & Finalize</h4>
              <p className="text-sm text-muted-foreground">Upload your reviewed Excel draft (with corrected Lớp 2 names) to extract the final keywords.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               <div className={cn("border rounded-lg p-4 space-y-3", rawFiles.length > 0 ? "bg-muted/10 border-green-500/30" : "border-destructive/30 bg-destructive/5")}>
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Raw Data</h5>
                    {rawFiles.length > 0 && <CheckCircle className="size-4 text-green-500" />}
                  </div>
                  <p className="text-sm font-medium truncate">{rawFiles.length > 0 ? `${rawFiles.length} files` : persistedRawFileName || "Missing File"}</p>
                  <Button variant="outline" size="sm" className="w-full text-[10px] h-7" asChild>
                    <label className="cursor-pointer">
                      Relink Files
                      <input type="file" multiple accept=".xlsx,.csv,.xls" className="hidden" onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          const fArray = Array.from(e.target.files);
                          setRawFiles(fArray); 
                          setPersistedRawFileName(fArray.map(f => f.name).join(', '));
                        }
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
                      <input type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => {
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
              <Button type="submit" className="flex-[2] gap-2 bg-green-600 hover:bg-green-700 text-white" disabled={loading || rawFiles.length === 0 || !reviewedDraftFile || !dictName}>
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

      {/* HS Code Interception Dialog */}
      <Dialog open={hsCheckOpen} onOpenChange={(open) => !hsCheckLoading && setHsCheckOpen(open)}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="size-5 text-amber-500" />
              Missing HS Taxonomy Records
            </DialogTitle>
            <DialogDescription>
              We found {unresolvedHsCodes.length} HS code(s) in your raw file that are not in the database and could not be found automatically. Please provide classification data before generating the draft.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {unresolvedHsCodes.map((item, index) => (
              <div key={item.hs_code} className="border p-4 rounded-lg bg-muted/10 space-y-3">
                <div className="font-mono font-bold border-b pb-2">HS: {item.hs_code}</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Dòng sản phẩm</label>
                    <Select 
                      value={item.dong_sp} 
                      onValueChange={(val) => {
                        const newCodes = [...unresolvedHsCodes];
                        newCodes[index].dong_sp = val;
                        setUnresolvedHsCodes(newCodes);
                      }}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {DONG_SP_OPTIONS.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Lớp 1 (Tên ngành)</label>
                    <Input 
                      placeholder="e.g. Bóng đèn LED"
                      value={item.industry_name}
                      onChange={(e) => {
                        const newCodes = [...unresolvedHsCodes];
                        newCodes[index].industry_name = e.target.value;
                        setUnresolvedHsCodes(newCodes);
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Phân loại (NC/LK)</label>
                    <Select 
                      value={item.default_type} 
                      onValueChange={(val) => {
                        const newCodes = [...unresolvedHsCodes];
                        newCodes[index].default_type = val;
                        setUnresolvedHsCodes(newCodes);
                      }}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NC">Nguyên chiếc (NC)</SelectItem>
                        <SelectItem value="LK">Linh kiện (LK)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setHsCheckOpen(false)} disabled={hsCheckLoading}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveUnresolvedHsCodes} 
              disabled={hsCheckLoading || unresolvedHsCodes.some(u => !u.industry_name.trim())}
              className="gap-2"
            >
              {hsCheckLoading ? <RefreshCw className="size-4 animate-spin" /> : <Database className="size-4" />}
              Save & Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default DictionaryGeneratorWizard;
