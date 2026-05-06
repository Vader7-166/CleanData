import { BrowserRouter, Routes, Route } from "react-router";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";
import { CleanData } from "./components/CleanData";
import { Dictionary } from "./components/Dictionary";
import { DictionaryGenerator } from "./components/DictionaryGenerator";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clean-data" element={<CleanData />} />
            <Route path="/dictionary" element={<Dictionary />} />
            <Route path="/dictionary-generator" element={<DictionaryGenerator />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}