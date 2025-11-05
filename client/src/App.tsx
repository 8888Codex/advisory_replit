import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
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
        <Route path="/" component={Landing} />
        <Route path="/home" component={Home} />
        <Route path="/welcome">
          <Redirect to="/" />
        </Route>
        <Route path="/marketing">
          <Redirect to="/" />
        </Route>
        <Route path="/onboarding" component={Onboarding} />
        <Route path="/experts" component={Experts} />
        <Route path="/categories" component={Categories} />
        <Route path="/chat/:id" component={Chat} />
        <Route path="/create" component={Create} />
        <Route path="/admin/experts" component={AdminExperts} />
        <Route path="/test-council" component={TestCouncil} />
        <Route path="/personas" component={Personas} />
        <Route path="/council-room/:sessionId" component={CouncilRoom} />
        <Route component={NotFound} />
      </Switch>
    </AnimatePresence>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <div className="min-h-screen bg-background text-foreground">
            <Header />
            <Router />
          </div>
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
