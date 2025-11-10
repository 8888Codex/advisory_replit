import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Mail, Linkedin, MousePointerClick, Globe } from "lucide-react";

interface CopyExamplesCardProps {
  data: {
    // New format (from enrichment) - lists
    headlines?: string[];
    emailSubjects?: string[];
    socialPosts?: string[];
    ctaButtons?: string[];
    adCopy?: string[];
    landingPageHero?: string[];
    // Old format (fallback) - single values
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
        {/* New format - Lists of copy examples */}
        {data.headlines && data.headlines.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <FileText className="w-4 h-4 text-primary" />
              Headlines
            </div>
            <div className="space-y-2">
              {data.headlines.map((headline, idx) => (
                <p key={idx} className="text-base font-semibold p-3 bg-gradient-to-r from-muted to-transparent rounded-md border-l-4 border-primary">
                  {headline}
                </p>
              ))}
            </div>
          </div>
        )}

        {data.emailSubjects && data.emailSubjects.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Mail className="w-4 h-4 text-primary" />
              Subject Lines de Email
            </div>
            <div className="space-y-2">
              {data.emailSubjects.map((subject, idx) => (
                <p key={idx} className="text-sm p-3 bg-muted rounded-md font-medium">
                  {subject}
                </p>
              ))}
            </div>
          </div>
        )}

        {data.ctaButtons && data.ctaButtons.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <MousePointerClick className="w-4 h-4 text-primary" />
              Call-to-Actions
            </div>
            <div className="flex flex-wrap gap-2">
              {data.ctaButtons.map((cta, idx) => (
                <Badge key={idx} variant="default" className="text-sm px-4 py-2">
                  {cta}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {data.socialPosts && data.socialPosts.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Linkedin className="w-4 h-4 text-primary" />
              Posts para Redes Sociais
            </div>
            <div className="space-y-2">
              {data.socialPosts.map((post, idx) => (
                <p key={idx} className="text-sm p-4 bg-muted/50 rounded-md whitespace-pre-line">
                  {post}
                </p>
              ))}
            </div>
          </div>
        )}

        {data.adCopy && data.adCopy.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Ads Copy</div>
            <div className="space-y-2">
              {data.adCopy.map((ad, idx) => (
                <p key={idx} className="text-sm p-3 bg-muted rounded-md">
                  {ad}
                </p>
              ))}
            </div>
          </div>
        )}

        {data.landingPageHero && data.landingPageHero.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Globe className="w-4 h-4 text-primary" />
              Hero Section para Landing Page
            </div>
            <div className="space-y-3">
              {data.landingPageHero.map((hero, idx) => (
                <div key={idx} className="p-4 bg-gradient-to-br from-primary/5 to-transparent rounded-lg border border-primary/20">
                  <Badge variant="outline" className="mb-2">Versão {idx + 1}</Badge>
                  <p className="text-sm whitespace-pre-line">{hero}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Old format (fallback) */}
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
