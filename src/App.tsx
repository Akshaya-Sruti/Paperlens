import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { PaperProvider } from "./lib/paper-context";
import { Home } from "./pages/Home";
import { PaperWorkspace } from "./pages/PaperWorkspace";
import { Upload } from "./pages/Upload";
import { Workspace } from "./pages/Workspace";

function App() {
  return (
    <PaperProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/workspace" element={<Workspace />} />
          <Route path="/workspace/:paperId" element={<PaperWorkspace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </PaperProvider>
  );
}

export default App;
