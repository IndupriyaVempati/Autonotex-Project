import React, { useState } from 'react';
import { Network, Sparkles, BookOpen } from 'lucide-react';
import UploadZone from './components/UploadZone.jsx';
import NotesView from './components/NotesView.jsx';
import KnowledgeGraph from './components/KnowledgeGraph.jsx';
import TutorModal from './components/TutorModal.jsx';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [notesData, setNotesData] = useState(null);
  const [tutorTopic, setTutorTopic] = useState(null);

  const handleAnalysisComplete = (data) => {
    setGraphData(data.graph);
    setNotesData(data.notes);
  };

  return (
    <div className="flex h-screen bg-prime text-white overflow-hidden selection:bg-accent/30">

      {/* Sidebar */}
      <aside className="w-64 border-r border-white/10 p-6 flex flex-col gap-8 hidden md:flex">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent to-blue-600 flex items-center justify-center shadow-lg shadow-accent/20">
            <Network className="text-white w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            Autonotex
          </h1>
        </div>

        <nav className="flex flex-col gap-2">
          <div className="p-3 rounded-lg bg-white/5 text-accent font-medium flex items-center gap-3 cursor-pointer border border-accent/20 glow">
            <Sparkles className="w-4 h-4" />
            <span>Agentic Workspace</span>
          </div>
          <div className="p-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors flex items-center gap-3 cursor-pointer">
            <BookOpen className="w-4 h-4" />
            <span>Library</span>
          </div>
        </nav>

        <div className="mt-auto pt-6 border-t border-white/10">
          <div className="p-4 rounded-xl bg-gradient-to-br from-accent/20 to-blue-500/10 border border-white/5">
            <p className="text-xs text-accent font-semibold mb-1">AGENT STATUS</p>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              <span className="text-sm text-gray-300">Active</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative">
        {/* Top Bar */}
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-prime/80 backdrop-blur-md sticky top-0 z-50">
          <div className="text-sm text-gray-400">
            Current Session: <span className="text-white">New Analysis</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10"></div>
        </header>

        {/* Content Area */}
        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-64px)] flex flex-col">
          {!graphData ? (
            <>
              <div className="mb-8">
                <h2 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-slate-500 bg-clip-text text-transparent mb-2">
                  Transform Content into Knowledge
                </h2>
                <p className="text-gray-400 text-lg max-w-2xl">
                  Upload your documents and let our Agentic AI generate interactive knowledge graphs for you.
                </p>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                <UploadZone onAnalysisComplete={handleAnalysisComplete} />
              </div>
            </>
          ) : (
            <div className="flex-1 min-h-0 flex gap-6">
              {/* Left: Knowledge Graph (60%) */}
              <div className="flex-[3] flex flex-col gap-4 h-full min-h-0">
                <div className="flex items-center justify-between shrink-0">
                  <h2 className="text-2xl font-semibold">Knowledge Graph</h2>
                  <button
                    onClick={() => setGraphData(null)}
                    className="text-sm px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/10"
                  >
                    Upload New File
                  </button>
                </div>
                <KnowledgeGraph data={graphData} />
              </div>

              {/* Right: Notes (40%) */}
              <div className="flex-[2] h-full min-h-0">
                <NotesView
                  notes={notesData || "# Generating notes..."}
                  onTopicClick={setTutorTopic}
                />
              </div>
            </div>
          )}
        </div>
      </main>

      {tutorTopic && (
        <TutorModal
          topic={tutorTopic}
          onClose={() => setTutorTopic(null)}
        />
      )}
    </div>
  );
}

export default App;
