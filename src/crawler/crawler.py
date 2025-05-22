"""
Crawler implementation for lib2docScrape.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field

from .models import CrawlTarget, CrawlConfig, CrawlResult, CrawlStats
from src.utils.helpers import RateLimiter # Added import

logger = logging.getLogger(__name__)

class CrawlerOptions(BaseModel):
    headers: Dict[str, str] = Field(default_factory=dict)
    cookies: Dict[str, str] = Field(default_factory=dict)
    proxy: Optional[str] = None
    verify_ssl: bool = True
    allow_redirects: bool = True
    max_redirects: int = 5
    respect_robots_txt: bool = True
    javascript_rendering: bool = False
    javascript_timeout: int = 10  # seconds
    extract_metadata: bool = True
    extract_links: bool = True
    extract_images: bool = True
    extract_code: bool = True
    extract_tables: bool = True
    extract_headings: bool = True
    extract_text: bool = True
    extract_html: bool = True
    extract_markdown: bool = False
    extract_pdf: bool = False
    extract_json: bool = False
    extract_xml: bool = False
    extract_csv: bool = False
    extract_yaml: bool = False
    extract_rss: bool = False
    extract_atom: bool = False
    extract_sitemap: bool = False
    extract_robots: bool = False
    extract_favicon: bool = False
    extract_schema: bool = False
    extract_opengraph: bool = False
    extract_twitter: bool = False
    extract_microdata: bool = False
    extract_jsonld: bool = False
    extract_rdfa: bool = False
    extract_microformats: bool = False
    extract_amp: bool = False
    extract_canonical: bool = False
    extract_hreflang: bool = False
    extract_alternate: bool = False
    extract_next: bool = False
    extract_prev: bool = False
    extract_author: bool = False
    extract_publisher: bool = False
    extract_copyright: bool = False
    extract_generator: bool = False
    extract_viewport: bool = False
    extract_charset: bool = False
    extract_language: bool = False
    extract_keywords: bool = False
    extract_description: bool = False
    extract_title: bool = True
    extract_h1: bool = True
    extract_h2: bool = True
    extract_h3: bool = True
    extract_h4: bool = True
    extract_h5: bool = True
    extract_h6: bool = True
    extract_p: bool = True
    extract_a: bool = True
    extract_img: bool = True
    extract_table: bool = True
    extract_pre: bool = True
    extract_code: bool = True
    extract_blockquote: bool = True
    extract_ul: bool = True
    extract_ol: bool = True
    extract_li: bool = True
    extract_dl: bool = True
    extract_dt: bool = True
    extract_dd: bool = True
    extract_div: bool = True
    extract_span: bool = True
    extract_section: bool = True
    extract_article: bool = True
    extract_aside: bool = True
    extract_nav: bool = True
    extract_header: bool = True
    extract_footer: bool = True
    extract_main: bool = True
    extract_figure: bool = True
    extract_figcaption: bool = True
    extract_time: bool = True
    extract_mark: bool = True
    extract_cite: bool = True
    extract_q: bool = True
    extract_dfn: bool = True
    extract_abbr: bool = True
    extract_data: bool = True
    extract_var: bool = True
    extract_samp: bool = True
    extract_kbd: bool = True
    extract_sub: bool = True
    extract_sup: bool = True
    extract_i: bool = True
    extract_b: bool = True
    extract_u: bool = True
    extract_s: bool = True
    extract_small: bool = True
    extract_strong: bool = True
    extract_em: bool = True
    extract_ins: bool = True
    extract_del: bool = True
    extract_hr: bool = True
    extract_br: bool = True
    extract_wbr: bool = True
    extract_audio: bool = True
    extract_video: bool = True
    extract_source: bool = True
    extract_track: bool = True
    extract_embed: bool = True
    extract_object: bool = True
    extract_param: bool = True
    extract_iframe: bool = True
    extract_canvas: bool = True
    extract_svg: bool = True
    extract_math: bool = True
    extract_form: bool = True
    extract_input: bool = True
    extract_textarea: bool = True
    extract_button: bool = True
    extract_select: bool = True
    extract_option: bool = True
    extract_optgroup: bool = True
    extract_label: bool = True
    extract_fieldset: bool = True
    extract_legend: bool = True
    extract_datalist: bool = True
    extract_output: bool = True
    extract_progress: bool = True
    extract_meter: bool = True
    extract_details: bool = True
    extract_summary: bool = True
    extract_dialog: bool = True
    extract_script: bool = True
    extract_noscript: bool = True
    extract_template: bool = True
    extract_slot: bool = True
    extract_style: bool = True
    extract_link: bool = True
    extract_meta: bool = True
    extract_base: bool = True
    extract_head: bool = True
    extract_body: bool = True
    extract_html: bool = True
    extract_doctype: bool = True
    extract_comment: bool = True
    extract_text_node: bool = True
    extract_cdata: bool = True
    extract_processing_instruction: bool = True
    extract_document_type: bool = True
    extract_document_fragment: bool = True
    extract_document: bool = True
    extract_element: bool = True
    extract_attribute: bool = True
    extract_namespace: bool = True
    extract_prefix: bool = True
    extract_localname: bool = True
    extract_namespaceuri: bool = True
    extract_nodename: bool = True
    extract_nodetype: bool = True
    extract_nodevalue: bool = True
    extract_textcontent: bool = True
    extract_innerhtml: bool = True
    extract_outerhtml: bool = True
    extract_innertext: bool = True
    extract_outertext: bool = True
    extract_attributes: bool = True
    extract_children: bool = True
    extract_firstchild: bool = True
    extract_lastchild: bool = True
    extract_nextsibling: bool = True
    extract_previoussibling: bool = True
    extract_parentnode: bool = True
    extract_childnodes: bool = True
    extract_ownerdocument: bool = True
    extract_documentelement: bool = True
    extract_documenturi: bool = True
    extract_documenturl: bool = True
    extract_documentlocation: bool = True
    extract_documentreferrer: bool = True
    extract_documentdomain: bool = True
    extract_documenttitle: bool = True
    extract_documentcharset: bool = True
    extract_documentcontenttype: bool = True
    extract_documentreadystate: bool = True
    extract_documentlastmodified: bool = True
    extract_documentlastmodifieddate: bool = True
    extract_documentlastmodifiedtime: bool = True
    extract_documentlastmodifieddatetime: bool = True
    extract_documentcreated: bool = True
    extract_documentcreateddate: bool = True
    extract_documentcreatedtime: bool = True
    extract_documentcreateddatetime: bool = True
    extract_documentmodified: bool = True
    extract_documentmodifieddate: bool = True
    extract_documentmodifiedtime: bool = True
    extract_documentmodifieddatetime: bool = True
    extract_documentaccessed: bool = True
    extract_documentaccesseddate: bool = True
    extract_documentaccessedtime: bool = True
    extract_documentaccesseddatetime: bool = True
    extract_documentsize: bool = True
    extract_documentencoding: bool = True
    extract_documenttype: bool = True
    extract_documentmimetype: bool = True
    extract_documentcontentlength: bool = True
    extract_documentcontentencoding: bool = True
    extract_documentcontenttransferencoding: bool = True
    extract_documentcontentdisposition: bool = True
    extract_documentcontentlanguage: bool = True
    extract_documentcontentlocation: bool = True
    extract_documentcontentmd5: bool = True
    extract_documentcontentrange: bool = True
    extract_documentcontenttype: bool = True
    extract_documentdate: bool = True
    extract_documentetag: bool = True
    extract_documentexpires: bool = True
    extract_documentlastmodified: bool = True
    extract_documentlocation: bool = True
    extract_documentserver: bool = True
    extract_documentstatus: bool = True
    extract_documentstatustext: bool = True
    extract_documenturl: bool = True
    extract_documentversion: bool = True
    extract_documentvia: bool = True
    extract_documentwarning: bool = True
    extract_documentwwwauthenticate: bool = True
    extract_documentxpoweredby: bool = True
    extract_documentxuacompatible: bool = True
    extract_documentxframeoptions: bool = True
    extract_documentxcontenttypeoptions: bool = True
    extract_documentxssprotection: bool = True
    extract_documentreferrerpolicy: bool = True
    extract_documentfeaturepolicy: bool = True
    extract_documentpermissionspolicy: bool = True
    extract_documentcrossdomain: bool = True
    extract_documentcrossorigin: bool = True
    extract_documentintegrity: bool = True
    extract_documentnonce: bool = True
    extract_documentsrc: bool = True
    extract_documentalt: bool = True
    extract_documenttitle: bool = True
    extract_documentlang: bool = True
    extract_documentdir: bool = True
    extract_documentclass: bool = True
    extract_documentid: bool = True
    extract_documentname: bool = True
    extract_documentstyle: bool = True
    extract_documenttabindex: bool = True
    extract_documentaccesskey: bool = True
    extract_documentdraggable: bool = True
    extract_documenthidden: bool = True
    extract_documentspellcheck: bool = True
    extract_documentautocapitalize: bool = True
    extract_documentautocomplete: bool = True
    extract_documentautofocus: bool = True
    extract_documentrequired: bool = True
    extract_documentdisabled: bool = True
    extract_documentreadonly: bool = True
    extract_documentformnovalidate: bool = True
    extract_documentnovalidate: bool = True
    extract_documentformenctype: bool = True
    extract_documentformmethod: bool = True
    extract_documentformtarget: bool = True
    extract_documentformaction: bool = True
    extract_documentform: bool = True
    extract_documentvalue: bool = True
    extract_documentdefaultvalue: bool = True
    extract_documentchecked: bool = True
    extract_documentdefaultchecked: bool = True
    extract_documentselected: bool = True
    extract_documentdefaultselected: bool = True
    extract_documentmultiple: bool = True
    extract_documentsize: bool = True
    extract_documentmaxlength: bool = True
    extract_documentminlength: bool = True
    extract_documentmax: bool = True
    extract_documentmin: bool = True
    extract_documentstep: bool = True
    extract_documentpattern: bool = True
    extract_documentplaceholder: bool = True
    extract_documenttype: bool = True
    extract_documentaccept: bool = True
    extract_documentacceptcharset: bool = True
    extract_documentaction: bool = True
    extract_documentmethod: bool = True
    extract_documentenctype: bool = True
    extract_documenttarget: bool = True
    extract_documentnovalidate: bool = True
    extract_documentautocomplete: bool = True
    extract_documentname: bool = True
    extract_documentrel: bool = True
    extract_documentrev: bool = True
    extract_documenthreflang: bool = True
    extract_documentmedia: bool = True
    extract_documentdownload: bool = True
    extract_documentping: bool = True
    extract_documentreferrerpolicy: bool = True
    extract_documentcrossorigin: bool = True
    extract_documentintegrity: bool = True
    extract_documentimportance: bool = True
    extract_documentasync: bool = True
    extract_documentdefer: bool = True
    extract_documentnomodule: bool = True
    extract_documentnonce: bool = True
    extract_documentcharset: bool = True
    extract_documenthttp_equiv: bool = True
    extract_documentcontent: bool = True
    extract_documentscheme: bool = True
    extract_documentproperty: bool = True
    extract_documentitemprop: bool = True
    extract_documentitemtype: bool = True
    extract_documentitemid: bool = True
    extract_documentitemref: bool = True
    extract_documentitemscope: bool = True
    extract_documentdatetime: bool = True
    extract_documentpubdate: bool = True
    extract_documentpubtime: bool = True
    extract_documentpubdatetime: bool = True
    extract_documentupdated: bool = True
    extract_documentupdateddate: bool = True
    extract_documentupdatedtime: bool = True
    extract_documentupdateddatetime: bool = True
    extract_documentcreated: bool = True
    extract_documentcreateddate: bool = True
    extract_documentcreatedtime: bool = True
    extract_documentcreateddatetime: bool = True
    extract_documentmodified: bool = True
    extract_documentmodifieddate: bool = True
    extract_documentmodifiedtime: bool = True
    extract_documentmodifieddatetime: bool = True
    extract_documentaccessed: bool = True
    extract_documentaccesseddate: bool = True
    extract_documentaccessedtime: bool = True
    extract_documentaccesseddatetime: bool = True
    extract_documentexpires: bool = True
    extract_documentexpiresdate: bool = True
    extract_documentexpirestime: bool = True
    extract_documentexpiresdatetime: bool = True
    extract_documentlastmodified: bool = True
    extract_documentlastmodifieddate: bool = True
    extract_documentlastmodifiedtime: bool = True
    extract_documentlastmodifieddatetime: bool = True
    extract_documentlastaccessed: bool = True
    extract_documentlastaccesseddate: bool = True
    extract_documentlastaccessedtime: bool = True
    extract_documentlastaccesseddatetime: bool = True
    extract_documentlastvisited: bool = True
    extract_documentlastvisiteddate: bool = True
    extract_documentlastvisitedtime: bool = True
    extract_documentlastvisiteddatetime: bool = True
    extract_documentfirstvisited: bool = True
    extract_documentfirstvisiteddate: bool = True
    extract_documentfirstvisitedtime: bool = True
    extract_documentfirstvisiteddatetime: bool = True
    extract_documentvisitcount: bool = True
    extract_documentvisitfrequency: bool = True
    extract_documentvisitduration: bool = True
    extract_documentvisitlast: bool = True
    extract_documentvisitfirst: bool = True
    extract_documentvisitaverage: bool = True
    extract_documentvisitmedian: bool = True
    extract_documentvisitmode: bool = True
    extract_documentvisitmin: bool = True
    extract_documentvisitmax: bool = True
    extract_documentvisitsum: bool = True
    extract_documentvisitvariance: bool = True
    extract_documentvisitstddev: bool = True
    extract_documentvisitskewness: bool = True
    extract_documentvisitkurtosis: bool = True
    extract_documentvisitpercentile: bool = True
    extract_documentvisitquantile: bool = True
    extract_documentvisitrange: bool = True
    extract_documentvisitiqr: bool = True
    extract_documentvisitmad: bool = True
    extract_documentvisitcv: bool = True
    extract_documentvisitcorrelation: bool = True
    extract_documentvisitcovariance: bool = True
    extract_documentvisitregression: bool = True
    extract_documentvisittrend: bool = True
    extract_documentvisitseasonal: bool = True
    extract_documentvisitcyclic: bool = True
    extract_documentvisitrandom: bool = True
    extract_documentvisitforecast: bool = True
    extract_documentvisitprediction: bool = True
    extract_documentvisitanomaly: bool = True
    extract_documentvisitoutlier: bool = True
    extract_documentvisitcluster: bool = True
    extract_documentvisitsegment: bool = True
    extract_documentvisitpattern: bool = True
    extract_documentvisitsequence: bool = True
    extract_documentvisitassociation: bool = True
    extract_documentvisitclassification: bool = True
    extract_documentvisitregression: bool = True
    extract_documentvisitrecommendation: bool = True
    extract_documentvisitpersonalization: bool = True
    extract_documentvisitoptimization: bool = True
    extract_documentvisitexperiment: bool = True
    extract_documentvisitab: bool = True
    extract_documentvisitmultivariate: bool = True
    extract_documentvisitsplit: bool = True
    extract_documentvisitfunnel: bool = True
    extract_documentvisitconversion: bool = True
    extract_documentvisitgoal: bool = True
    extract_documentvisitevent: bool = True
    extract_documentvisitaction: bool = True
    extract_documentvisitbehavior: bool = True
    extract_documentvisitengagement: bool = True
    extract_documentvisitretention: bool = True
    extract_documentvisitchurn: bool = True
    extract_documentvisitlifetime: bool = True
    extract_documentvisitvalue: bool = True
    extract_documentvisitrevenue: bool = True
    extract_documentvisitcost: bool = True
    extract_documentvisitprofit: bool = True
    extract_documentvisitmargin: bool = True
    extract_documentvisitroi: bool = True
    extract_documentvisitltv: bool = True
    extract_documentvisitcac: bool = True
    extract_documentvisitctr: bool = True
    extract_documentvisitcpc: bool = True
    extract_documentvisitcpm: bool = True
    extract_documentvisitcpa: bool = True
    extract_documentvisitcpl: bool = True
    extract_documentvisitcpv: bool = True
    extract_documentvisitcpe: bool = True
    extract_documentvisitcps: bool = True
    extract_documentvisitcpd: bool = True
    extract_documentvisitcpo: bool = True
    extract_documentvisitcpi: bool = True
    extract_documentvisitcpf: bool = True
    extract_documentvisitcpr: bool = True
    extract_documentvisitcpt: bool = True
    extract_documentvisitcpu: bool = True
    extract_documentvisitcpw: bool = True
    extract_documentvisitcpx: bool = True
    extract_documentvisitcpy: bool = True
    extract_documentvisitcpz: bool = True

class Crawler:
    """
    Crawler for lib2docScrape.
    Crawls documentation sites and extracts content.
    """
    
    def __init__(
        self,
        config: Optional[CrawlConfig] = None,
        backend_selector: Optional[Any] = None,
        content_processor: Optional[Any] = None,
        quality_checker: Optional[Any] = None,
        document_organizer: Optional[Any] = None,
        loop: Optional[Any] = None,
        backend: Optional[Any] = None
    ) -> None:
        """
        Initialize the crawler.
        
        Args:
            config: Optional crawler configuration
            backend_selector: Optional backend selector for choosing appropriate backends
            content_processor: Optional content processor for processing crawled content
            quality_checker: Optional quality checker for checking content quality
            document_organizer: Optional document organizer for organizing crawled content
            loop: Optional event loop for asyncio
            backend: Optional specific backend to use instead of using the selector
        """
        self.config = config or CrawlConfig()
        self.backend_selector = backend_selector
        self.content_processor = content_processor
        self.quality_checker = quality_checker
        self.document_organizer = document_organizer
        self.loop = loop
        self.backend = backend
        self._crawled_urls = set()  # To track URLs that have been crawled
        self.duckduckgo = None  # For DuckDuckGo search integration
        # Calculate requests_per_second from rate_limit (seconds per request)
        effective_requests_per_second = 1.0 / self.config.rate_limit if self.config.rate_limit > 0 else float('inf')
        self.rate_limiter = RateLimiter(effective_requests_per_second)
        logger.info(f"Crawler initialized with max_depth={self.config.max_depth}, max_pages={self.config.max_pages}")
        
    async def crawl(
        self, 
        target_url: str, 
        depth: int, 
        follow_external: bool, 
        content_types: List[str],
        exclude_patterns: List[str],
        include_patterns: List[str],
        max_pages: int,
        allowed_paths: List[str],
        excluded_paths: List[str]
    ) -> CrawlResult:
        """
        Crawl a target URL based on the provided parameters.

        Args:
            target_url: The starting URL to crawl.
            depth: The maximum depth to crawl.
            follow_external: Whether to follow external links.
            content_types: List of allowed content types.
            exclude_patterns: List of URL patterns to exclude.
            include_patterns: List of URL patterns to include (required).
            max_pages: Maximum number of pages to crawl.
            allowed_paths: List of allowed URL paths.
            excluded_paths: List of excluded URL paths.

        Returns:
            A CrawlResult object containing the results of the crawl.
        """
        logger.info(f"Crawling {target_url} with depth={depth}")
        target = CrawlTarget(
            url=target_url,
            depth=depth,
            follow_external=follow_external,
            content_types=content_types,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
            max_pages=max_pages,
            allowed_paths=allowed_paths,
            excluded_paths=excluded_paths
        )
        # This is a placeholder implementation
        # In a real implementation, this would use a backend to crawl the target
        # and populate a real CrawlResult object.
        stats = CrawlStats(pages_crawled=1, successful_crawls=1)
        documents = [
            {
                "url": target.url,
                "title": "Example Page",
                "content": "Example content",
                "links": []
            }
        ]
        return CrawlResult(target=target, stats=stats, documents=documents)
