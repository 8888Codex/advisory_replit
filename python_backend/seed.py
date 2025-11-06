"""
Seed marketing legends with their cognitive clones
"""
from models import ExpertCreate, ExpertType, CategoryType
from storage import MemStorage
from prompts.legends import LEGENDS_PROMPTS

async def seed_legends(storage: MemStorage):
    """Seed the 18 marketing & growth experts as high-fidelity cognitive clones"""
    
    legends_data = [
        # MARKETING CATEGORY (Traditional marketing strategy)
        {
            "name": "Philip Kotler",
            "title": "O Pai do Marketing Moderno",
            "bio": "Professor, autor e consultor considerado o maior especialista mundial em marketing estratégico. Criador dos 4Ps e pioneiro em segmentação de mercado.",
            "expertise": ["Estratégia de Marketing", "Segmentação", "4Ps", "Brand Positioning", "Marketing Internacional"],
            "system_prompt": LEGENDS_PROMPTS["philip_kotler"],
            "avatar": "/attached_assets/stock_images/Philip Kotler.png",
            "category": CategoryType.MARKETING,
        },
        {
            "name": "David Ogilvy",
            "title": "O Pai da Publicidade",
            "bio": "Fundador da Ogilvy & Mather, criou campanhas icônicas e revolucionou o copywriting. Mestre em construir marcas de luxo e comunicação persuasiva.",
            "expertise": ["Copywriting", "Brand Building", "Direct Response", "Creative Strategy", "Luxury Marketing"],
            "system_prompt": LEGENDS_PROMPTS["david_ogilvy"],
            "avatar": "/attached_assets/stock_images/David Ogilvy .png",
            "category": CategoryType.MARKETING,
        },
        {
            "name": "Claude C. Hopkins",
            "title": "Pioneiro do Marketing Científico",
            "bio": "Revolucionou a publicidade no início do século XX ao introduzir testes mensuráveis e rastreamento de ROI. Autor de 'Scientific Advertising'.",
            "expertise": ["Scientific Advertising", "A/B Testing", "ROI Tracking", "Direct Response", "Teste e Mensuração"],
            "system_prompt": LEGENDS_PROMPTS["claude_hopkins"],
            "avatar": "/attached_assets/stock_images/Claude_Hopkins_vintage_portrait_b074ce60.png",
            "category": CategoryType.MARKETING,
        },
        {
            "name": "David Aaker",
            "title": "O Arquiteto do Brand Equity",
            "bio": "Criador do Brand Equity Model (1991) - 5 components framework (loyalty, awareness, perceived quality, associations, proprietary assets). Vice Chairman da Prophet consultancy. Professor Emeritus UC Berkeley. Autor de 17+ livros sobre branding. Apple, Amazon, Coca-Cola = classic examples de positive brand equity.",
            "expertise": ["Brand Equity", "Brand Identity", "Brand Leadership", "5 Components Model", "Brands as Assets", "Long-Term Value"],
            "system_prompt": LEGENDS_PROMPTS["david_aaker"],
            "avatar": "/attached_assets/stock_images/David Aaker.png",
            "category": CategoryType.MARKETING,
        },
        {
            "name": "Jay Levinson",
            "title": "O Pai do Guerrilla Marketing",
            "bio": "Autor de 'Guerrilla Marketing' (1984) - TIME Magazine Top 25 Best Business Book. 21M+ copies sold, 62 languages. Revolucionou marketing para small businesses. 200+ marketing weapons documented - mais de metade são FREE. Focus: time, energy, imagination > money.",
            "expertise": ["Guerrilla Marketing", "200 Marketing Weapons", "Low-Cost High-Impact", "Creativity Over Budget", "Unconventional Tactics"],
            "system_prompt": LEGENDS_PROMPTS["jay_levinson"],
            "avatar": "/attached_assets/stock_images/Jay Levinson.png",
            "category": CategoryType.MARKETING,
        },
        
        # POSITIONING CATEGORY
        {
            "name": "Al Ries & Jack Trout",
            "title": "Os Arquitetos do Posicionamento Estratégico",
            "bio": "Dupla lendária que criou as 22 Leis Imutáveis do Marketing e revolucionou o conceito de posicionamento. Foco laser em ocupar posição única na mente do consumidor.",
            "expertise": ["Posicionamento", "22 Leis Imutáveis", "First-Mover Advantage", "Foco Estratégico", "Mente do Consumidor"],
            "system_prompt": LEGENDS_PROMPTS["al_ries_jack_trout"],
            "avatar": "/attached_assets/stock_images/Al Rie.png",
            "category": CategoryType.POSITIONING,
        },
        {
            "name": "Simon Sinek",
            "title": "O Profeta do Start With Why",
            "bio": "Autor 'Start With Why' (2009). TED Talk 'How Great Leaders Inspire Action': 40M+ views (one of most-watched ever). Golden Circle framework: WHY (purpose) → HOW (process) → WHAT (product). Apple 'Think Different': WHY-first exemplar. Think Different campaign: $90M budget, Apple near bankruptcy → +20% revenue year 1, 2.8%→5% market share.",
            "expertise": ["Start With Why", "Golden Circle", "WHY-HOW-WHAT", "Inside-Out Communication", "Purpose-Driven Leadership"],
            "system_prompt": LEGENDS_PROMPTS["simon_sinek"],
            "avatar": "/attached_assets/stock_images/Simon Sinek.png",
            "category": CategoryType.POSITIONING,
        },
        {
            "name": "Donald Miller",
            "title": "O Mestre do StoryBrand Framework",
            "bio": "Criador do StoryBrand Framework (SB7) baseado no Hero's Journey. Autor de 'Building a StoryBrand' (bestseller). Clientes: Intel, Charity Water, Chick-fil-A, TOMS, TREK, Tempur Sealy. Thousands companies from startups to Fortune 500. Multiple cases de $1M→$20M+ growth em <2 anos.",
            "expertise": ["StoryBrand SB7", "Hero's Journey Marketing", "Clear Messaging", "Customer as Hero", "Brand as Guide", "7-Part Framework"],
            "system_prompt": LEGENDS_PROMPTS["donald_miller"],
            "avatar": "/attached_assets/stock_images/Donald Miller.png",
            "category": CategoryType.POSITIONING,
        },
        
        # DIRECT RESPONSE CATEGORY
        {
            "name": "Dan Kennedy",
            "title": "O Rei do Direct Response Marketing",
            "bio": "Copywriter lendário e consultor multi-milionário. Criador do Magnetic Marketing e das 10 Commandments of Copy. Mestre em funis de conversão e maximização de LTV.",
            "expertise": ["Direct Response", "Magnetic Marketing", "Sales Letters", "Maximização LTV", "Copywriting de Conversão"],
            "system_prompt": LEGENDS_PROMPTS["dan_kennedy"],
            "avatar": "/attached_assets/stock_images/Dan Kennedy.png",
            "category": CategoryType.DIRECT_RESPONSE,
        },
        {
            "name": "Eugene Schwartz",
            "title": "O Arquiteto do Desejo em Massa",
            "bio": "Autor de 'Breakthrough Advertising' (1966), considerado a bíblia do copywriting persuasivo. Criador dos frameworks 5 Stages of Awareness e 5 Stages of Market Sophistication. Livro vendido por $125-900 quando fora de catálogo, republicado tornou-se essencial para todo copywriter. Desenvolveu Mass Desire Principle e 13 Intensification Techniques que definem copywriting moderno.",
            "expertise": ["Breakthrough Advertising", "5 Stages of Awareness", "Market Sophistication", "Mass Desire", "Copywriting Psicológico", "Headline Frameworks", "Intensification Techniques"],
            "system_prompt": LEGENDS_PROMPTS["eugene_schwartz"],
            "avatar": "/attached_assets/stock_images/Eugene Schwartz.png",
            "category": CategoryType.DIRECT_RESPONSE,
        },
        {
            "name": "Drayton Bird",
            "title": "O Protégé de Ogilvy - Mestre do Direct Response",
            "bio": "David Ogilvy: 'Drayton Bird knows more about direct marketing than anyone in the world.' International Vice-Chairman O&M Direct, Creative Director building world's largest direct marketing agency network. Autor 'Commonsense Direct Marketing' (1982) - UK #1 bestseller EVERY YEAR since 1982, 17 languages, 5 editions. £1.5M+ from <2K prospects via integrated campaigns.",
            "expertise": ["Direct Response", "Testing Obsession", "Commonsense Direct Marketing", "Results-Driven", "Customer Understanding", "Integrated Campaigns"],
            "system_prompt": LEGENDS_PROMPTS["drayton_bird"],
            "avatar": "/attached_assets/stock_images/Drayton Bird.png",
            "category": CategoryType.DIRECT_RESPONSE,
        },
        {
            "name": "Robert Cialdini",
            "title": "O Cientista da Persuasão Ética",
            "bio": "Autor de 'Influence: Psychology of Persuasion' (1984, 5M+ copies sold, 44 languages). Professor Arizona State University. Pesquisador de 35+ anos em persuasion science. Criador dos 6 Principles of Influence testados em centenas de experiments. Consultor de Google, Microsoft, Coca-Cola.",
            "expertise": ["6 Principles of Influence", "Reciprocity", "Social Proof", "Scarcity", "Authority", "Commitment/Consistency", "Liking", "Ethical Persuasion"],
            "system_prompt": LEGENDS_PROMPTS["robert_cialdini"],
            "avatar": "/attached_assets/stock_images/Robert Cialdini.png",
            "category": CategoryType.DIRECT_RESPONSE,
        },
        {
            "name": "Daniel Kahneman",
            "title": "O Padrinho da Behavioral Economics",
            "bio": "Nobel Prize Economics 2002 por integrar psychology em economics (nunca fez curso de economics!). Autor 'Thinking Fast and Slow' (2011 bestseller). Com Amos Tversky, criou Prospect Theory (1979, most-cited economics paper). Loss aversion: losses hurt 2x more than equivalent gains. Bat & Ball problem demonstra System 1 substitution.",
            "expertise": ["System 1 and System 2", "Prospect Theory", "Loss Aversion", "Cognitive Biases", "Heuristics", "Behavioral Economics"],
            "system_prompt": LEGENDS_PROMPTS["daniel_kahneman"],
            "avatar": "/attached_assets/stock_images/Daniel Kahneman.png",
            "category": CategoryType.DIRECT_RESPONSE,
        },
        
        # CONTENT CATEGORY
        {
            "name": "Seth Godin",
            "title": "Visionário do Permission Marketing",
            "bio": "Autor best-seller e guru do marketing moderno. Criador dos conceitos Purple Cow e Tribes, pioneiro em permission marketing e storytelling digital.",
            "expertise": ["Permission Marketing", "Purple Cow", "Tribes", "Storytelling Digital", "Nicho e Posicionamento"],
            "system_prompt": LEGENDS_PROMPTS["seth_godin"],
            "avatar": "/attached_assets/stock_images/seth godin.png",
            "category": CategoryType.CONTENT,
        },
        {
            "name": "Ann Handley",
            "title": "A Rainha do Content Marketing",
            "bio": "Chief Content Officer da MarketingProfs, autora best-seller de 'Everybody Writes'. Pioneira em content marketing e evangelista de writing com empatia e utilidade extrema.",
            "expertise": ["Content Marketing", "Everybody Writes", "Brand Voice", "Editorial Strategy", "Human Writing"],
            "system_prompt": LEGENDS_PROMPTS["ann_handley"],
            "avatar": "/attached_assets/stock_images/Ann Handley.png",
            "category": CategoryType.CONTENT,
        },
        
        # SEO CATEGORY
        {
            "name": "Neil Patel",
            "title": "O Mestre do SEO Data-Driven",
            "bio": "Co-fundador da NP Digital e Ubersuggest, reconhecido como top influencer em digital marketing. Expert em SEO, content marketing e growth hacking orientado por dados.",
            "expertise": ["SEO", "Ubersuggest", "Content Decay", "Technical SEO", "Data-Driven Marketing"],
            "system_prompt": LEGENDS_PROMPTS["neil_patel"],
            "avatar": "/attached_assets/stock_images/neil patel.png",
            "category": CategoryType.SEO,
        },
        
        # SOCIAL CATEGORY
        {
            "name": "Gary Vaynerchuk",
            "title": "Rei do Marketing Digital e Hustle",
            "bio": "Empreendedor serial, investidor e especialista em redes sociais. Conhecido por sua abordagem direta, foco em personal branding e 'day trading attention'.",
            "expertise": ["Social Media", "Personal Branding", "Day Trading Attention", "Content Creation", "Entrepreneurship"],
            "system_prompt": LEGENDS_PROMPTS["gary_vaynerchuk"],
            "avatar": "/attached_assets/stock_images/Gary Vaynerchuk .jpg",
            "category": CategoryType.SOCIAL,
        },
        
        # GROWTH CATEGORY
        {
            "name": "Jay Abraham",
            "title": "O $9.4 Billion Man",
            "bio": "Conhecido como 'The $9.4 Billion Man' - documentou ter gerado $75B+ em revenue increases para 10.000+ empresas em 400+ indústrias. Criador do framework '3 Ways to Grow Business', Parthenon Strategy (múltiplos pilares de revenue), e Strategy of Preeminence (value-first, advisor mindset). Autor de 'Getting Everything You Can Out of All You've Got'. Consultor de Tony Robbins, Daymond John, e centenas de Fortune 500. Master de identificar hidden assets e aplicar best practices cross-industry.",
            "expertise": ["3 Ways to Grow Business", "Strategy of Preeminence", "Parthenon Principles", "Geometric Growth", "Funnel Vision", "Lifetime Value Optimization", "Strategic Joint Ventures"],
            "system_prompt": LEGENDS_PROMPTS["jay_abraham"],
            "avatar": "/attached_assets/stock_images/Jay Abraham.png",
            "category": CategoryType.GROWTH,
        },
    ]
    
    for legend in legends_data:
        expert_data = ExpertCreate(
            name=legend["name"],
            title=legend["title"],
            bio=legend["bio"],
            expertise=legend["expertise"],
            systemPrompt=legend["system_prompt"],
            avatar=legend["avatar"],
            category=legend["category"],
            expertType=ExpertType.HIGH_FIDELITY  # These are high-fidelity clones
        )
        await storage.create_expert(expert_data)
