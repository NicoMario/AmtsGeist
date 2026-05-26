"""FastAPI-App — die HTTP-Schnittstelle des AmtsGeist-Inferenz-Backends."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .audit import write_audit
from .config import Settings, get_settings
from .llm.client import OllamaClient, OllamaError
from .llm.router import CascadeRouter
from .schemas import (
    BatchTriageItem,
    BatchTriageRequest,
    BatchTriageResponse,
    BriefingRequest,
    BriefingResponse,
    DraftReplyRequest,
    DraftReplyResponse,
    SummarizeRequest,
    SummarizeResponse,
    TriageRequest,
    TriageResponse,
)
from .services import briefing as briefing_service
from .services import draft as draft_service
from .services import summarize as summarize_service
from .services import triage as triage_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = OllamaClient(settings.ollama_base_url, settings.request_timeout_s)
    app.state.settings = settings
    app.state.router = CascadeRouter(client, settings)
    yield


app = FastAPI(
    title="AmtsGeist Inferenz-Backend",
    description="Souveränes 'Gehirn' für den Outlook-Assistenten der deutschen Verwaltung.",
    version=__version__,
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(OllamaError)
async def _ollama_error_handler(_: Request, exc: OllamaError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


def _settings_of(request: Request) -> Settings:
    return request.app.state.settings


def _router_of(request: Request) -> CascadeRouter:
    return request.app.state.router


@app.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "slm_model": s.slm_model,
        "llm_model": s.llm_model,
        "cascade": s.enable_cascade,
        "pii_pseudonymization": s.enable_pii_pseudonymization,
    }


@app.post("/triage", response_model=TriageResponse)
async def triage_endpoint(req: TriageRequest, request: Request) -> TriageResponse:
    s, router = _settings_of(request), _router_of(request)
    t0 = time.perf_counter()
    resp = await triage_service.triage(req, router, s)
    write_audit(
        s,
        endpoint="/triage",
        model_used=resp.model_used,
        escalated=resp.escalated,
        latency_ms=(time.perf_counter() - t0) * 1000,
        category=resp.result.category.value,
        priority=resp.result.priority,
    )
    return resp


@app.post("/triage/batch", response_model=BatchTriageResponse)
async def triage_batch_endpoint(
    req: BatchTriageRequest, request: Request
) -> BatchTriageResponse:
    s, router = _settings_of(request), _router_of(request)
    t0 = time.perf_counter()
    responses = await triage_service.triage_many(req.emails, router, s)
    items = [
        BatchTriageItem(result=r.result, model_used=r.model_used, escalated=r.escalated)
        for r in responses
    ]
    write_audit(
        s,
        endpoint="/triage/batch",
        model_used="(batch)",
        escalated=any(r.escalated for r in responses),
        latency_ms=(time.perf_counter() - t0) * 1000,
        n=len(items),
    )
    return BatchTriageResponse(items=items)


@app.post("/draft-reply", response_model=DraftReplyResponse)
async def draft_reply_endpoint(
    req: DraftReplyRequest, request: Request
) -> DraftReplyResponse:
    s, router = _settings_of(request), _router_of(request)
    t0 = time.perf_counter()
    resp = await draft_service.draft_reply(req, router, s)
    write_audit(
        s,
        endpoint="/draft-reply",
        model_used=resp.model_used,
        escalated=False,
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return resp


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(
    req: SummarizeRequest, request: Request
) -> SummarizeResponse:
    s, router = _settings_of(request), _router_of(request)
    t0 = time.perf_counter()
    resp = await summarize_service.summarize(req, router, s)
    write_audit(
        s,
        endpoint="/summarize",
        model_used=resp.model_used,
        escalated=resp.escalated,
        latency_ms=(time.perf_counter() - t0) * 1000,
        n_emails=len(req.emails),
    )
    return resp


@app.post("/briefing", response_model=BriefingResponse)
async def briefing_endpoint(req: BriefingRequest, request: Request) -> BriefingResponse:
    s, router = _settings_of(request), _router_of(request)
    t0 = time.perf_counter()
    resp = await briefing_service.briefing(req, router, s)
    write_audit(
        s,
        endpoint="/briefing",
        model_used=resp.model_used,
        escalated=False,
        latency_ms=(time.perf_counter() - t0) * 1000,
        n_events=len(req.events),
    )
    return resp
