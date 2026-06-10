"""Alta manual de un usuario de la beta (FASE 2).

Resuelve el Riot ID a puuid (account-v1) y lo inserta/reactiva en
``usuarios_beta`` para que el poller empiece a seguirle.

Uso (dentro del contenedor api o worker):
    python -m app.worker.registrar "Nombre#TAG"
    python -m app.worker.registrar "Nombre#TAG" --baja     # desactivar
"""
import asyncio
import sys

from sqlalchemy import select

from app.core.config import settings
from app.db import sesion
from app.models import UsuarioBeta
from app.services.riot_client import riot_client


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or "#" not in args[0]:
        print('Uso: python -m app.worker.registrar "Nombre#TAG" [--baja]')
        sys.exit(1)
    riot_id = args[0].strip()
    baja = "--baja" in sys.argv

    nombre, tag = riot_id.split("#", 1)
    puuid = asyncio.run(riot_client.get_puuid(nombre.strip(), tag.strip()))

    with sesion() as s:
        u = s.scalar(select(UsuarioBeta).where(UsuarioBeta.puuid == puuid))
        if u is None:
            u = UsuarioBeta(puuid=puuid, riot_id=riot_id, region=settings.riot_platform, activo=not baja)
            s.add(u)
            accion = "dado de alta"
        else:
            u.riot_id = riot_id
            u.activo = not baja
            accion = "desactivado" if baja else "reactivado/actualizado"
        s.commit()
    print(f"[registrar] {riot_id} {accion} (puuid {puuid[:12]}…)")


if __name__ == "__main__":
    main()
