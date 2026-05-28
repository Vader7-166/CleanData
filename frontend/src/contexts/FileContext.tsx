import React, { createContext, useContext, useState, ReactNode } from 'react';

interface FileContextProps {
  dictionaryRawFiles: File[];
  setDictionaryRawFiles: (files: File[]) => void;
  dictionaryDraftFile: File | null;
  setDictionaryDraftFile: (file: File | null) => void;
  cleanDataFiles: File[];
  setCleanDataFiles: (files: File[]) => void;
}

const FileContext = createContext<FileContextProps | undefined>(undefined);

export const FileProvider = ({ children }: { children: ReactNode }) => {
  const [dictionaryRawFiles, setDictionaryRawFiles] = useState<File[]>([]);
  const [dictionaryDraftFile, setDictionaryDraftFile] = useState<File | null>(null);
  const [cleanDataFiles, setCleanDataFiles] = useState<File[]>([]);

  return (
    <FileContext.Provider value={{
      dictionaryRawFiles,
      setDictionaryRawFiles,
      dictionaryDraftFile,
      setDictionaryDraftFile,
      cleanDataFiles,
      setCleanDataFiles
    }}>
      {children}
    </FileContext.Provider>
  );
};

export const useFileContext = () => {
  const context = useContext(FileContext);
  if (!context) {
    throw new Error('useFileContext must be used within a FileProvider');
  }
  return context;
};
