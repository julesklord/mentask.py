Análisis de robustez y usabilidad
Lo que está muy bien hecho
La arquitectura en general es sólida y se ve claramente una visión a largo plazo. El orchestrator con async generator de eventos es el patrón correcto para este tipo de agente — reactivo, testeable, extensible. El schema.py con Pydantic v2 es limpio. El TrustManager está bien pensado. El sistema de memoria jerárquica (global/local/standard knowledge hub) es una feature seria que casi ningún agente CLI tiene. El security.py con SafetyLevel granular es profesional. El ContextCompressor inyectándose en el serializer de historial es un detalle elegante. HistoryManager con path traversal protection y rolling context window — bien. ConfigManager con keyring + fallback a env var + detección de legacy file inseguro — muy bien.

Bugs que crashean en producción (no opiniones, hechos)
1. reset_session no existe en SessionManager
commands.py lo llama en 5 lugares distintos: /clear, /reset, /model, /load, /auth. El método no está definido en ninguna parte del archivo session.py. Todo comando que modifique el modelo o resetee sesión lanza AttributeError en runtime.
2. /stats crashea por referencia muerta
pythonf"📝 Files: [bold]{self.agent.dispatcher.modified_files_count}[/bold]"
dispatcher era del sistema viejo (ToolDispatcher). ChatAgent ya no lo tiene — fue reemplazado por self.tools (ToolRegistry) y self.orchestrator. AttributeError garantizado en cada /stats.
3. Historial nunca se persiste en la arquitectura nueva
HistoryManager.save_session() espera list[types.Content] del SDK de Gemini. El orquestrador trabaja con list[Message] (Pydantic interno). ChatAgent._save_history pasa chat_session.get_history() del SDK, pero ese chat_session nunca recibe ningún mensaje — solo generate_response (stateless) es usado por el orchestrator. El chat_session creado en ensure_session está huérfano. Resultado: el historial nunca se guarda, y al reiniciar el agente siempre empieza desde cero aunque diga que "reanuda sesión".
4. Compactación nunca se dispara
pythonlast_usage = history[-1].metadata.get("usage")
if not self._is_compacting and last_usage and last_usage.input_tokens > ...
AssistantMessage guarda usage como campo directo (msg.usage), no en metadata. metadata es un dict vacío por defecto. last_usage siempre es None. La compactación automática está muerta.
5. Path escape + directorio trusted = ejecución silenciosa sin bloqueo
pythonsecurity_warning = f"PATH ESCAPE ATTEMPT: {str(e)}"
# ... más abajo:
if is_dir_trusted and security_warning:
    yield {"type": "warning", "content": f"TRUSTED EXECUTION WITH WARNING: {security_warning}"}
# herramienta se ejecuta igual
Si el directorio está en trusted, un path escape (../../etc/passwd) genera solo un warning y sigue ejecutando. El trust debería bypassar la confirmación interactiva, no el análisis de seguridad.
6. _compact_history — argumento posicional mal
pythonraw_summary_response = await self.generate_response(
    history=history,
    tools_schema=[],
    config=types.GenerateContentConfig(...)
)
Firma real: generate_response(self, history, tools_schema, config=None). El primer argumento es posicional, no keyword. Puede funcionar en Python por el keyword arg, pero tools_schema pasado como keyword podría fallar dependiendo de la versión. Menor, pero inconsistente.

Problemas de usabilidad
No hay streaming real. El orquestrador llama generate_response que es una llamada completa y bloqueante. El renderer tiene toda la infraestructura de Live/streaming pero el "text" event llega de golpe al final. El usuario ve pantalla en blanco durante todo el tiempo que el modelo está pensando, y luego aparece todo el texto de un golpe. Con modelos lentos como gemini-2.5-pro esto puede ser 10-15 segundos de silencio total.
Dos sistemas de conversación en paralelo que no hablan entre sí. session.ensure_session() crea un chat_session stateful del SDK. session.generate_response() es stateless y gestiona historial manualmente. El orchestrator usa solo el segundo. El primero se crea, carga historial guardado (que ya está desactualizado por el punto 3), y nunca se usa. Esto también significa que el contexto del sistema prompt se construye dos veces (en _setup_system_prompt vía self.messages Y en _build_config vía context.build_system_instruction()).
No hay /memory. El agente puede gestionar memoria vía herramientas, pero el usuario no puede leer ni escribir memoria directamente desde el CLI sin preguntarle al agente que lo haga, lo cual consume tokens y requiere que el agente tome una decisión de herramienta.
No hay /plan. El plan .askgem_plan.md se inyecta en el contexto silenciosamente pero no hay forma de verlo, limpiarlo o editarlo desde el CLI.
/model sin args lista modelos pero no tiene paginación — Gemini tiene 40+ modelos disponibles en la API, eso va a desbordar el terminal sin filtrado.

Qué le agregaría
Prioridad inmediata (desbloqueantes):
reset_session en SessionManager — una línea: self.chat_session = None para forzar recreación en el próximo ensure_session. Sin eso 5 comandos están muertos.
Unificar los dos sistemas de conversación. Elegir uno: o el SDK stateful (chat_session) o el stateless manual (generate_response + self.messages). Los dos juntos crean deuda técnica sin valor. El stateless es más flexible para compactación y multi-provider, así que elegiría ese, pero entonces hay que actualizar HistoryManager para serializar Message Pydantic en lugar de types.Content.
Streaming real en generate_response usando aio.models.generate_content_stream(). El renderer ya está listo para recibirlo.
Features de valor real:
/memory [read|add|reset] [scope] — interfaz directa a MemoryManager sin pasar por el agente.
/plan [show|clear] — mostrar el contenido de .askgem_plan.md o borrarlo.
/backup — antes de cualquier write_file o edit_file en modo auto, copiar el original a ~/.askgem/backups/ con timestamp. get_backups_dir() ya existe en paths.py — está todo preparado pero nadie lo usa.
Capa de abstracción de provider. Ya que el objetivo es multi-provider (klai), una clase BaseProvider con métodos generate(messages, tools, config) → AsyncGenerator[event] y stream(...) desacoplaría completamente el orchestrator del SDK de Google. Implementaciones: GeminiProvider, AnthropicProvider, OpenAIProvider. El cambio en settings.json de provider: "gemini" a provider: "claude" cambiaría el backend completo sin tocar el orchestrator ni el renderer.
/diff para ediciones de archivos. Antes de aplicar un edit_file, mostrar un diff coloreado con rich.syntax de lo que cambiaría. El usuario ve exactamente qué va a modificar, no solo "AskGem quiere usar edit_file con path=X". Esto haría que el ask_confirmation del renderer fuera genuinamente útil en lugar de mostrar el texto crudo del reemplazo.
Rate limit visual. Cuando el exponential backoff se activa, el renderer debería mostrar una barra de progreso con countdown en lugar de solo el mensaje de warning. Con modelos free tier que tienen límites de RPM estrictos esto es importante.