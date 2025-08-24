def build_executive_text(kpis: dict) -> str:
    utilization = kpis.get("utilization_pct", 0.0)
    loss_pct = kpis.get("loss_pct", 0.0)
    delays = kpis.get("delays_count", 0)
    complaints = kpis.get("complaints_count", 0)
    production = kpis.get("production_30d_m2", 0.0)
    orders = kpis.get("orders_30d_m2", 0.0)

    trend = "estável"
    if utilization >= 90:
        trend = "acima do planejado"
    elif utilization < 70:
        trend = "abaixo do planejado"

    return (
        f"Produção consolidada de {production:.0f} m² nos últimos 30 dias, com utilização do forno {utilization:.1f}% ({trend}). "
        f"As perdas acumuladas representam {loss_pct:.1f}% da produção. Foi registrado {delays} atraso(s) e {complaints} reclamação(ões) no período. "
        f"Pedidos no período somam {orders:.0f} m². Reforçar ações de redução de perdas e atenção às causas de atrasos."
    )
