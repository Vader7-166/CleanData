import React from 'react';
import { useNavigate } from 'react-router-dom';
import DictionaryGeneratorWizard from './DictionaryGeneratorWizard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Sparkles, Zap, Search, FileText } from 'lucide-react';

const DictionaryGenerator = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">AI Dictionary Generator</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Create high-quality product dictionaries automatically using AI clustering and LLM labeling.
        </p>
      </div>
      
      <DictionaryGeneratorWizard onComplete={() => {
        setTimeout(() => {
          navigate('/dictionary');
        }, 2000);
      }} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="flex flex-col items-center text-center space-y-2 p-4">
          <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
            <Zap className="size-6" />
          </div>
          <h4 className="font-bold text-sm">1. Clustering</h4>
          <p className="text-xs text-muted-foreground">Similar products are grouped using TF-IDF and DBSCAN algorithms.</p>
        </div>
        <div className="flex flex-col items-center text-center space-y-2 p-4">
          <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
            <Sparkles className="size-6" />
          </div>
          <h4 className="font-bold text-sm">2. LLM Labeling</h4>
          <p className="text-xs text-muted-foreground">Llama 3.1 analyzes clusters to assign human-readable category names.</p>
        </div>
        <div className="flex flex-col items-center text-center space-y-2 p-4">
          <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
            <Search className="size-6" />
          </div>
          <h4 className="font-bold text-sm">3. Manual Review</h4>
          <p className="text-xs text-muted-foreground">Verify and adjust the generated category names in Excel.</p>
        </div>
        <div className="flex flex-col items-center text-center space-y-2 p-4">
          <div className="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
            <FileText className="size-6" />
          </div>
          <h4 className="font-bold text-sm">4. Extraction</h4>
          <p className="text-xs text-muted-foreground">Relevant keywords are extracted to build your final dictionary.</p>
        </div>
      </div>
    </div>
  );
};

export default DictionaryGenerator;
