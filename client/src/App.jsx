import React, { useState } from 'react';
import { Network, Sparkles, BookOpen, CheckSquare } from 'lucide-react';
import UploadZone from './components/UploadZone.jsx';
import SubjectNotesPanel from './components/SubjectNotesPanel.jsx';
import QuizSelection from './components/QuizSelection.jsx';
import QuizTaker from './components/QuizTaker.jsx';
import QuizAnalysis from './components/QuizAnalysis.jsx';
import NotesView from './components/NotesView.jsx';
import KnowledgeGraph from './components/KnowledgeGraph.jsx';
import TutorModal from './components/TutorModal.jsx';
import ConceptDetailsPanel from './components/ConceptDetailsPanel.jsx';
import QuestionsView from './components/QuestionsView.jsx';
import DiagramsView from './components/DiagramsView.jsx';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [notesData, setNotesData] = useState(null);
  const [questionsData, setQuestionsData] = useState(null);
  const [docId, setDocId] = useState(null);
  const [tutorTopic, setTutorTopic] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [activeView, setActiveView] = useState('graph');
  const [sourceDiagrams, setSourceDiagrams] = useState([]);
  const [homeMode, setHomeMode] = useState('upload');
  const [quizMode, setQuizMode] = useState(null); // null, 'selection', 'taking', 'analysis'
  const [quizResult, setQuizResult] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);

  const stripMermaidBlocks = (text) => {
    if (!text) return text;
    return text.replace(/```mermaid[\s\S]*?```/g, '').trim();
  };

  const handleAnalysisComplete = (data) => {
    setGraphData(data.graph || { nodes: [], edges: [] });
    setNotesData(data.notes);
    setQuestionsData(data.questions || []);
    setDocId(data.doc_id);
    setSourceDiagrams(data.source_diagrams || []);
    if (data.mode === 'subject') {
      setActiveView('summary');
    } else {
      setActiveView('graph');
    }
  };

  const handleNodeClick = (node) => {
    setSelectedConcept(node.data.label);
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
          
          <div className="pt-4 border-t border-white/10">
            <div className="text-xs text-gray-500 mb-2">NOTES INPUT</div>
            <button
              onClick={() => {
                setGraphData(null);
                setNotesData(null);
                setQuestionsData(null);
                setDocId(null);
                setSelectedConcept(null);
                setActiveView('graph');
                setHomeMode('upload');
                setQuizMode(null);
              }}
              className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 border ${
                homeMode === 'upload' && !quizMode
                  ? 'bg-accent/20 text-accent border-accent/40'
                  : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Upload Notes</span>
            </button>
            <button
              onClick={() => {
                setGraphData(null);
                setNotesData(null);
                setQuestionsData(null);
                setDocId(null);
                setSelectedConcept(null);
                setActiveView('graph');
                setHomeMode('subject');
                setQuizMode(null);
              }}
              className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 border mt-2 ${
                homeMode === 'subject' && !quizMode
                  ? 'bg-accent/20 text-accent border-accent/40'
                  : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Subject Notes</span>
            </button>
            <button
              onClick={() => {
                setGraphData(null);
                setNotesData(null);
                setQuestionsData(null);
                setDocId(null);
                setSelectedConcept(null);
                setQuizMode('selection');
              }}
              className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 border mt-2 ${
                quizMode
                  ? 'bg-accent/20 text-accent border-accent/40'
                  : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
              }`}
            >
              <CheckSquare className="w-4 h-4" />
              <span>Quizzes</span>
            </button>
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
            Current Session: <span className="text-white">{docId ? 'Active' : 'New Analysis'}</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10"></div>
        </header>

        {/* Content Area */}
        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-64px)] flex flex-col">
          {/* Quiz Mode */}
          {quizMode === 'selection' && (
            <QuizSelection
              onQuizStart={(subject) => {
                setSelectedSubject(subject);
                setQuizMode('taking');
              }}
            />
          )}

          {quizMode === 'taking' && (
            <QuizTaker
              subject={selectedSubject}
              onQuizComplete={(result) => {
                setQuizResult(result);
                setQuizMode('analysis');
              }}
              onBack={() => {
                setQuizMode('selection');
                setSelectedSubject(null);
              }}
            />
          )}

          {quizMode === 'analysis' && (
            <QuizAnalysis
              quizResult={quizResult}
              onRetake={() => {
                setQuizMode('taking');
              }}
              onBack={() => {
                setQuizMode('selection');
                setSelectedSubject(null);
              }}
            />
          )}

          {/* Notes Mode */}
          {!quizMode && !graphData ? (
            <>
              <div className="mb-8">
                <h2 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-slate-500 bg-clip-text text-transparent mb-2">
                  Transform Content into Knowledge
                </h2>
                <p className="text-gray-400 text-lg max-w-2xl">
                  Upload your documents and let our Agentic AI generate interactive knowledge graphs, comprehensive notes, and study questions.
                </p>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                {homeMode === 'upload' ? (
                  <UploadZone onAnalysisComplete={handleAnalysisComplete} />
                ) : (
                  <SubjectNotesPanel onAnalysisComplete={handleAnalysisComplete} />
                )}
              </div>
            </>
          ) : !quizMode && (
            <div className="flex-1 min-h-0 flex gap-6 flex-col lg:flex-row">
              <div className="flex-1 flex flex-col gap-4 min-h-0">
                <div className="flex items-center justify-between shrink-0">
                  <h2 className="text-2xl font-semibold">Knowledge Workspace</h2>
                  <button
                    onClick={() => {
                      setGraphData(null);
                      setNotesData(null);
                      setQuestionsData(null);
                      setDocId(null);
                      setSelectedConcept(null);
                      setActiveView('graph');
                      setHomeMode('upload');
                    }}
                    className="text-sm px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/10"
                  >
                    Upload New File
                  </button>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {[
                    { id: 'summary', label: 'Summary' },
                    { id: 'diagrams', label: 'Diagrams' },
                    { id: 'questions', label: 'Questions' },
                    { id: 'graph', label: 'Knowledge Graph' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveView(tab.id)}
                      className={`text-sm px-4 py-2 rounded-lg border transition-colors ${
                        activeView === tab.id
                          ? 'bg-accent/20 text-accent border-accent/40'
                          : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {activeView === 'graph' && (
                  <div className="flex-1 min-h-0 rounded-lg overflow-hidden border border-white/10 bg-slate-800/40">
                    <KnowledgeGraph data={graphData} onNodeClick={handleNodeClick} />
                  </div>
                )}

                {activeView === 'questions' && (
                  <div className="flex-1 min-h-0 overflow-y-auto rounded-lg border border-white/10 bg-slate-800/40">
                    <QuestionsView questions={questionsData} docId={docId} />
                  </div>
                )}

                {activeView === 'summary' && (
                  <div className="flex-1 min-h-0 rounded-lg overflow-hidden border border-white/10 bg-slate-800/40">
                    <NotesView notes={stripMermaidBlocks(notesData) || "# Generating notes..."} />
                  </div>
                )}

                {activeView === 'diagrams' && (
                  <div className="flex-1 min-h-0 rounded-lg overflow-hidden border border-white/10 bg-slate-800/40 p-4">
                    <DiagramsView notes={notesData} sourceDiagrams={sourceDiagrams} />
                  </div>
                )}
              </div>

              {/* Concept Details Panel */}
              {selectedConcept && activeView === 'graph' && (
                <ConceptDetailsPanel 
                  conceptLabel={selectedConcept}
                  docId={docId}
                  onClose={() => setSelectedConcept(null)}
                />
              )}
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
