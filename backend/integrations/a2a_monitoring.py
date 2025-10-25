"""
A2A Monitoring and Observability
Comprehensive logging, metrics, and tracing for agent workflows

Features:
- Message flow tracing (track messages across agents)
- Performance metrics (latency, throughput)
- Agent health monitoring
- Workflow analytics
- Error tracking and alerting
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class A2AMessageTracer:
    """
    Tracks message flow across agents for debugging and analytics
    """
    
    def __init__(self):
        """Initialize message tracer"""
        self.traces = {}  # trace_id -> trace data
        self.active_traces = set()
        logger.info("A2A Message Tracer initialized")
    
    def start_trace(
        self,
        trace_id: str,
        workflow_name: str,
        initiator: str
    ) -> str:
        """
        Start a new trace for a workflow
        
        Args:
            trace_id: Unique trace identifier
            workflow_name: Name of workflow being traced
            initiator: Who/what started this workflow
        
        Returns:
            trace_id for reference
        """
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "initiator": initiator,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "messages": [],
            "agents_involved": set(),
            "status": "active"
        }
        self.active_traces.add(trace_id)
        
        logger.info(f"Started trace: {trace_id} for workflow: {workflow_name}")
        return trace_id
    
    def log_message(
        self,
        trace_id: str,
        sender: str,
        recipient: str,
        payload_summary: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Log a message in the trace
        
        Args:
            trace_id: Trace this message belongs to
            sender: Message sender
            recipient: Message recipient
            payload_summary: Brief description of payload
            timestamp: Message timestamp (default: now)
        """
        if trace_id not in self.traces:
            logger.warning(f"Trace {trace_id} not found, creating new trace")
            self.start_trace(trace_id, "unknown", "unknown")
        
        trace = self.traces[trace_id]
        
        message_log = {
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "sender": sender,
            "recipient": recipient,
            "payload_summary": payload_summary,
            "sequence_number": len(trace["messages"]) + 1
        }
        
        trace["messages"].append(message_log)
        trace["agents_involved"].add(sender)
        trace["agents_involved"].add(recipient)
        
        logger.debug(f"Trace {trace_id}: {sender} -> {recipient}")
    
    def end_trace(
        self,
        trace_id: str,
        status: str = "completed",
        error: Optional[str] = None
    ):
        """
        End a trace
        
        Args:
            trace_id: Trace to end
            status: Final status (completed, failed, timeout)
            error: Error message if failed
        """
        if trace_id not in self.traces:
            logger.warning(f"Trace {trace_id} not found")
            return
        
        trace = self.traces[trace_id]
        trace["end_time"] = datetime.now().isoformat()
        trace["status"] = status
        trace["agents_involved"] = list(trace["agents_involved"])
        
        if error:
            trace["error"] = error
        
        # Calculate duration
        start = datetime.fromisoformat(trace["start_time"])
        end = datetime.fromisoformat(trace["end_time"])
        trace["duration_seconds"] = (end - start).total_seconds()
        
        self.active_traces.discard(trace_id)
        
        logger.info(
            f"Ended trace: {trace_id} - Status: {status} "
            f"({trace['duration_seconds']:.2f}s, {len(trace['messages'])} messages)"
        )
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace data"""
        return self.traces.get(trace_id)
    
    def get_active_traces(self) -> List[str]:
        """Get list of active trace IDs"""
        return list(self.active_traces)
    
    def export_trace(self, trace_id: str, filepath: str):
        """Export trace to JSON file"""
        trace = self.get_trace(trace_id)
        if not trace:
            logger.error(f"Trace {trace_id} not found")
            return
        
        with open(filepath, 'w') as f:
            json.dump(trace, f, indent=2)
        
        logger.info(f"Exported trace {trace_id} to {filepath}")


class A2AMetricsCollector:
    """
    Collects performance metrics for A2A agents and workflows
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.agent_metrics = defaultdict(lambda: {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_latency_ms": 0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0,
            "errors": []
        })
        
        self.workflow_metrics = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_duration_seconds": 0,
            "min_duration_seconds": float('inf'),
            "max_duration_seconds": 0
        })
        
        self.start_time = datetime.now()
        logger.info("A2A Metrics Collector initialized")
    
    def record_agent_call(
        self,
        agent_name: str,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Record metrics for an agent call
        
        Args:
            agent_name: Name of agent
            latency_ms: Call latency in milliseconds
            success: Whether call succeeded
            error: Error message if failed
        """
        metrics = self.agent_metrics[agent_name]
        
        metrics["total_calls"] += 1
        if success:
            metrics["successful_calls"] += 1
        else:
            metrics["failed_calls"] += 1
            if error:
                metrics["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error
                })
        
        metrics["total_latency_ms"] += latency_ms
        metrics["min_latency_ms"] = min(metrics["min_latency_ms"], latency_ms)
        metrics["max_latency_ms"] = max(metrics["max_latency_ms"], latency_ms)
    
    def record_workflow_execution(
        self,
        workflow_name: str,
        duration_seconds: float,
        success: bool
    ):
        """
        Record metrics for a workflow execution
        
        Args:
            workflow_name: Name of workflow
            duration_seconds: Total workflow duration
            success: Whether workflow succeeded
        """
        metrics = self.workflow_metrics[workflow_name]
        
        metrics["total_executions"] += 1
        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
        
        metrics["total_duration_seconds"] += duration_seconds
        metrics["min_duration_seconds"] = min(
            metrics["min_duration_seconds"],
            duration_seconds
        )
        metrics["max_duration_seconds"] = max(
            metrics["max_duration_seconds"],
            duration_seconds
        )
    
    def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get metrics for a specific agent
        
        Returns:
            Dict with agent metrics including average latency, success rate, etc.
        """
        if agent_name not in self.agent_metrics:
            return {}
        
        metrics = self.agent_metrics[agent_name]
        
        # Calculate derived metrics
        if metrics["total_calls"] > 0:
            avg_latency = metrics["total_latency_ms"] / metrics["total_calls"]
            success_rate = metrics["successful_calls"] / metrics["total_calls"]
        else:
            avg_latency = 0
            success_rate = 0
        
        return {
            "agent_name": agent_name,
            "total_calls": metrics["total_calls"],
            "successful_calls": metrics["successful_calls"],
            "failed_calls": metrics["failed_calls"],
            "success_rate": f"{success_rate * 100:.1f}%",
            "avg_latency_ms": f"{avg_latency:.2f}",
            "min_latency_ms": metrics["min_latency_ms"],
            "max_latency_ms": metrics["max_latency_ms"],
            "recent_errors": metrics["errors"][-5:]  # Last 5 errors
        }
    
    def get_workflow_metrics(self, workflow_name: str) -> Dict[str, Any]:
        """Get metrics for a specific workflow"""
        if workflow_name not in self.workflow_metrics:
            return {}
        
        metrics = self.workflow_metrics[workflow_name]
        
        # Calculate derived metrics
        if metrics["total_executions"] > 0:
            avg_duration = (
                metrics["total_duration_seconds"] / metrics["total_executions"]
            )
            success_rate = (
                metrics["successful_executions"] / metrics["total_executions"]
            )
        else:
            avg_duration = 0
            success_rate = 0
        
        return {
            "workflow_name": workflow_name,
            "total_executions": metrics["total_executions"],
            "successful_executions": metrics["successful_executions"],
            "failed_executions": metrics["failed_executions"],
            "success_rate": f"{success_rate * 100:.1f}%",
            "avg_duration_seconds": f"{avg_duration:.2f}",
            "min_duration_seconds": metrics["min_duration_seconds"],
            "max_duration_seconds": metrics["max_duration_seconds"]
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall system summary"""
        uptime = datetime.now() - self.start_time
        
        total_agent_calls = sum(
            m["total_calls"] for m in self.agent_metrics.values()
        )
        total_workflow_executions = sum(
            m["total_executions"] for m in self.workflow_metrics.values()
        )
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split('.')[0],
            "total_agent_calls": total_agent_calls,
            "total_workflow_executions": total_workflow_executions,
            "agents_monitored": len(self.agent_metrics),
            "workflows_monitored": len(self.workflow_metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    def print_report(self):
        """Print comprehensive metrics report"""
        print("\n" + "="*80)
        print("A2A METRICS REPORT")
        print("="*80)
        
        summary = self.get_summary()
        print(f"\nSystem Uptime: {summary['uptime_formatted']}")
        print(f"Total Agent Calls: {summary['total_agent_calls']}")
        print(f"Total Workflow Executions: {summary['total_workflow_executions']}")
        
        print("\n" + "-"*80)
        print("AGENT METRICS")
        print("-"*80)
        
        for agent_name in sorted(self.agent_metrics.keys()):
            metrics = self.get_agent_metrics(agent_name)
            print(f"\n{agent_name}:")
            print(f"  Calls: {metrics['total_calls']} "
                  f"(✓ {metrics['successful_calls']} / ✗ {metrics['failed_calls']})")
            print(f"  Success Rate: {metrics['success_rate']}")
            print(f"  Latency: avg={metrics['avg_latency_ms']}ms, "
                  f"min={metrics['min_latency_ms']:.0f}ms, "
                  f"max={metrics['max_latency_ms']:.0f}ms")
        
        print("\n" + "-"*80)
        print("WORKFLOW METRICS")
        print("-"*80)
        
        for workflow_name in sorted(self.workflow_metrics.keys()):
            metrics = self.get_workflow_metrics(workflow_name)
            print(f"\n{workflow_name}:")
            print(f"  Executions: {metrics['total_executions']} "
                  f"(✓ {metrics['successful_executions']} / "
                  f"✗ {metrics['failed_executions']})")
            print(f"  Success Rate: {metrics['success_rate']}")
            print(f"  Duration: avg={metrics['avg_duration_seconds']}s, "
                  f"min={metrics['min_duration_seconds']:.2f}s, "
                  f"max={metrics['max_duration_seconds']:.2f}s")
        
        print("\n" + "="*80)


class A2AHealthMonitor:
    """
    Monitors health of agents and system components
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize health monitor
        
        Args:
            check_interval_seconds: How often to check health
        """
        self.check_interval = check_interval_seconds
        self.health_status = {}
        self.last_check_time = {}
        logger.info(f"A2A Health Monitor initialized (check every {check_interval_seconds}s)")
    
    async def check_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """
        Check health of a specific agent
        
        Args:
            agent_name: Name of agent to check
        
        Returns:
            Health status dict
        """
        now = datetime.now()
        
        # Simple health check - can be extended with actual agent ping
        health = {
            "agent_name": agent_name,
            "status": "healthy",
            "last_check": now.isoformat(),
            "responsive": True,
            "errors": []
        }
        
        self.health_status[agent_name] = health
        self.last_check_time[agent_name] = now
        
        return health
    
    async def check_system_health(
        self,
        agent_registry,
        llm_client
    ) -> Dict[str, Any]:
        """
        Check overall system health
        
        Args:
            agent_registry: Registry to check agent availability
            llm_client: LLM client to check backend connectivity
        
        Returns:
            System health dict
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        # Check LLM backend
        try:
            llm_healthy = llm_client.health_check()
            health["components"]["llm_backend"] = {
                "status": "healthy" if llm_healthy else "unhealthy",
                "responsive": llm_healthy
            }
        except Exception as e:
            health["components"]["llm_backend"] = {
                "status": "error",
                "error": str(e)
            }
            health["overall_status"] = "degraded"
        
        # Check agent availability
        available_agents = list(agent_registry.agents.keys())
        health["components"]["agents"] = {
            "total": len(available_agents),
            "available": available_agents,
            "status": "healthy" if available_agents else "unhealthy"
        }
        
        return health
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of all health checks"""
        return {
            "timestamp": datetime.now().isoformat(),
            "agents_monitored": len(self.health_status),
            "agent_health": self.health_status
        }


# Global singleton instances for easy access
_tracer = None
_metrics = None
_health_monitor = None


def get_tracer() -> A2AMessageTracer:
    """Get global message tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = A2AMessageTracer()
    return _tracer


def get_metrics() -> A2AMetricsCollector:
    """Get global metrics collector instance"""
    global _metrics
    if _metrics is None:
        _metrics = A2AMetricsCollector()
    return _metrics


def get_health_monitor() -> A2AHealthMonitor:
    """Get global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = A2AHealthMonitor()
    return _health_monitor


if __name__ == "__main__":
    # Demo monitoring capabilities
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    print("A2A MONITORING DEMO")
    print("="*80)
    
    # Initialize monitoring
    tracer = get_tracer()
    metrics = get_metrics()
    
    # Simulate some activity
    print("\nSimulating agent activity...")
    
    trace_id = tracer.start_trace("demo-trace", "client_intake", "demo_user")
    
    tracer.log_message(
        trace_id,
        "orchestrator",
        "paralegal-client-communication",
        "Process client message"
    )
    
    metrics.record_agent_call(
        "paralegal-client-communication",
        latency_ms=150.5,
        success=True
    )
    
    tracer.log_message(
        trace_id,
        "paralegal-client-communication",
        "paralegal-legal-researcher",
        "Get case research"
    )
    
    metrics.record_agent_call(
        "paralegal-legal-researcher",
        latency_ms=320.8,
        success=True
    )
    
    tracer.end_trace(trace_id, status="completed")
    
    metrics.record_workflow_execution(
        "client_intake",
        duration_seconds=0.5,
        success=True
    )
    
    # Print reports
    print("\n" + "="*80)
    print("TRACE REPORT")
    print("="*80)
    
    trace = tracer.get_trace(trace_id)
    print(f"\nTrace ID: {trace['trace_id']}")
    print(f"Workflow: {trace['workflow_name']}")
    print(f"Duration: {trace['duration_seconds']:.2f}s")
    print(f"Messages: {len(trace['messages'])}")
    print(f"Agents involved: {', '.join(trace['agents_involved'])}")
    
    metrics.print_report()
    
    print("\n✅ Monitoring demo complete!")
