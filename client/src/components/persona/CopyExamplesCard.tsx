import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Mail, Linkedin, MousePointerClick, Globe } from "lucide-react";

interface CopyExamplesCardProps {
  data: {
    headline?: string;
    emailSubject?: string;
    linkedinPost?: string;
    cta?: string;
    landingPageCopy?: string;
  } | null;
}

export function CopyExamplesCard({ data }: CopyExamplesCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Exemplos de Copy
          </CardTitle>
          <CardDescription>
            Disponível apenas na Persona Completa
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          Exemplos de Copy
        </CardTitle>
        <CardDescription>
          Copy pronta para usar baseada nos insights da persona
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {data.headline && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <FileText className="w-4 h-4 text-primary" />
              Headline
            </div>
            <p className="text-lg font-semibold p-4 bg-muted rounded-md border-l-4 border-primary">
              {data.headline}
            </p>
          </div>
        )}

        {data.emailSubject && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Mail className="w-4 h-4 text-primary" />
              Assunto de Email
            </div>
            <p className="text-sm p-3 bg-muted rounded-md font-medium">
              {data.emailSubject}
            </p>
          </div>
        )}

        {data.linkedinPost && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Linkedin className="w-4 h-4 text-primary" />
              Post LinkedIn
            </div>
            <p className="text-sm p-4 bg-muted rounded-md whitespace-pre-line">
              {data.linkedinPost}
            </p>
          </div>
        )}

        {data.cta && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <MousePointerClick className="w-4 h-4 text-primary" />
              Call-to-Action
            </div>
            <Badge variant="default" className="text-base px-4 py-2">
              {data.cta}
            </Badge>
          </div>
        )}

        {data.landingPageCopy && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Globe className="w-4 h-4 text-primary" />
              Copy para Landing Page
            </div>
            <p className="text-sm p-4 bg-muted rounded-md whitespace-pre-line">
              {data.landingPageCopy}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
