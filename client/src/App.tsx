import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Header } from "@/components/Header";
import { AnimatePresence } from "framer-motion";
import NotFound from "@/pages/not-found";
import Landing from "@/pages/Landing";
import Home from "@/pages/Home";
import Experts from "@/pages/Experts";
import Categories from "@/pages/Categories";
import Chat from "@/pages/Chat";
import Create from "@/pages/Create";
import AdminExperts from "@/pages/AdminExperts";
import Onboarding from "@/pages/Onboarding";
import TestCouncil from "@/pages/TestCouncil";
import Personas from "@/pages/Personas";
import CouncilRoom from "@/pages/CouncilRoom";
import PersonaDashboard from "@/pages/PersonaDashboard";
import Analytics from "@/pages/Analytics";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Settings from "@/pages/Settings";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";

function Redirect({ to }: { to: string }) {
  const [, setLocation] = useLocation();
  setLocation(to);
  return null;
}

function Router() {
  const [location] = useLocation();
  
  return (
    <AnimatePresence mode="wait">
      <Switch location={location} key={location}>
        {/* Public Routes */}
        <Route path="/" component={Landing} />
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/forgot-password" component={ForgotPassword} />
        <Route path="/reset-password" component={ResetPassword} />
        
        {/* Legacy Redirects */}
        <Route path="/welcome">
          <Redirect to="/" />
        </Route>
        <Route path="/marketing">
          <Redirect to="/" />
        </Route>
        
        {/* Protected Routes */}
        <Route path="/settings">
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        </Route>
        <Route path="/home">
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        </Route>
        <Route path="/onboarding">
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        </Route>
        <Route path="/persona-dashboard">
          <ProtectedRoute>
            <PersonaDashboard />
          </ProtectedRoute>
        </Route>
        <Route path="/analytics">
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        </Route>
        <Route path="/experts">
          <ProtectedRoute>
            <Experts />
          </ProtectedRoute>
        </Route>
        <Route path="/categories">
          <ProtectedRoute>
            <Categories />
          </ProtectedRoute>
        </Route>
        <Route path="/chat/:id">
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        </Route>
        <Route path="/create">
          <ProtectedRoute>
            <Create />
          </ProtectedRoute>
        </Route>
        <Route path="/admin/experts">
          <ProtectedRoute>
            <AdminExperts />
          </ProtectedRoute>
        </Route>
        <Route path="/test-council">
          <ProtectedRoute>
            <TestCouncil />
          </ProtectedRoute>
        </Route>
        <Route path="/personas">
          <ProtectedRoute>
            <Personas />
          </ProtectedRoute>
        </Route>
        <Route path="/council-room/:sessionId">
          <ProtectedRoute>
            <CouncilRoom />
          </ProtectedRoute>
        </Route>
        
        {/* 404 Catch-all */}
        <Route component={NotFound} />
      </Switch>
    </AnimatePresence>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <TooltipProvider>
            <div className="min-h-screen bg-background text-foreground">
              <Header />
              <Router />
            </div>
            <Toaster />
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
