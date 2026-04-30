import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import MeetingPage from "./pages/MeetingPage";
import LoginPage from "./pages/LoginPage";

function Header() {
  const { user, logout } = useAuth();
  return (
    <header className="bg-banxico-700 text-white px-6 py-3 shadow-sm">
      <div className="max-w-6xl mx-auto flex items-center gap-6">
        <Link to="/" className="font-semibold tracking-wide">
          Simulador Junta Banxico
        </Link>
        {user && (
          <nav className="text-sm flex gap-4 opacity-90">
            <Link to="/" className="hover:underline">Inicio</Link>
            <Link to="/chat" className="hover:underline">Chat 1-a-1</Link>
            <Link to="/meeting" className="hover:underline">Junta</Link>
          </nav>
        )}
        <div className="ml-auto flex items-center gap-3 text-sm">
          {user ? (
            <>
              <span className="opacity-90">{user.display_name}</span>
              <button
                onClick={logout}
                className="text-xs px-2 py-1 rounded border border-white/30 hover:bg-white/10"
              >
                Salir
              </button>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return <p className="p-6 text-stone-500">Cargando…</p>;
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        path="/"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/chat"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route
        path="/chat/:agentId"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route
        path="/chat/session/:sessionId"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route
        path="/meeting"
        element={
          <RequireAuth>
            <MeetingPage />
          </RequireAuth>
        }
      />
      <Route
        path="/meeting/:meetingId"
        element={
          <RequireAuth>
            <MeetingPage />
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-full flex flex-col">
        <Header />
        <main className="flex-1">
          <AppRoutes />
        </main>
      </div>
    </AuthProvider>
  );
}
