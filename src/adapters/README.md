# Adapters Layer - Guía de Uso

Esta capa implementa el patrón **Adapter** (parte de la Arquitectura Hexagonal) para desacoplar el código de negocio de las implementaciones específicas de servicios externos.

## 📦 Estructura

```
adapters/
├── __init__.py                  # Exports principales
├── llm/
│   ├── __init__.py
│   ├── base.py                 # LLMAdapter interface (en core/interfaces.py)
│   ├── openapi_adapter.py      # Implementación OpenAI
│   └── example_usage.py        # Ejemplos de uso
├── messaging/
│   ├── __init__.py
│   ├── base.py                 # MessagingAdapter interface (en core/interfaces.py)
│   └── twilio_adapter.py       # Implementación Twilio
└── storage/
    ├── __init__.py
    ├── base.py                 # StorageAdapter interface
    ├── local_adapter.py        # Implementación en memoria
    └── example_usage.py        # Ejemplos de uso
```

## 🎯 Interfaces Core

Las interfaces están definidas en `src/core/interfaces.py`:

### `LLMAdapter`

Define el contrato para proveedores de LLM (Language Model):

```python
class LLMAdapter(ABC):
    @abstractmethod
    def get_agent_decision(
        self, user_text: str, context: ConversationContext | None = None
    ) -> AgentDecision:
        """Obtiene decisión estructurada del agente."""
        pass
    
    @abstractmethod
    def humanize_response(
        self, user_text: str, action: str, base_message: str, vehicles: list[dict] | None = None
    ) -> str:
        """Humaniza una respuesta estructurada."""
        pass
    
    @abstractmethod
    def generate_financing_response(self, user_text: str, vehicle_price: float) -> str:
        """Genera opciones de financiamiento."""
        pass
    
    @abstractmethod
    def generate_kavak_info_response(self, user_text: str, kavak_info: str, query: str) -> str:
        """Genera respuesta sobre información de Kavak."""
        pass
```

### `MessagingAdapter`

Define el contrato para sistemas de mensajería (WhatsApp, SMS, etc.):

```python
class MessagingAdapter(ABC):
    @abstractmethod
    def parse_webhook(self, event: dict) -> str:
        """Parsea webhook entrante."""
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> str:
        """Envía mensaje al usuario."""
        pass
```

### `StorageAdapter`

Define el contrato para almacenamiento de contexto de conversación:

```python
class StorageAdapter(ABC):
    @abstractmethod
    async def get(self, session_id: str) -> ConversationContext | None:
        """Obtiene el contexto de una sesión."""
        pass
    
    @abstractmethod
    async def get_or_create(self, session_id: str) -> ConversationContext:
        """Obtiene o crea el contexto de una sesión."""
        pass
    
    @abstractmethod
    async def save(self, context: ConversationContext) -> None:
        """Guarda el contexto de una sesión."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Elimina el contexto de una sesión."""
        pass
    
    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión."""
        pass
    
    @abstractmethod
    async def clear_all(self) -> int:
        """Elimina todas las sesiones."""
        pass
```

## 🚀 Uso de Adapters

### OpenAIAdapter (LLM)

### Importación

```python
from src.adapters import OpenAIAdapter, get_default_openai_adapter
```

### Opción 1: Usar el adapter por defecto (recomendado)

```python
# Usa variables de entorno: OPENAI_API_KEY, OPENAI_API_BASE_URL
adapter = get_default_openai_adapter()

decision = adapter.get_agent_decision("Busco un Toyota Corolla 2023")
print(decision.action)  # AgentAction.SEARCH_CARS
```

### Opción 2: Configuración custom

```python
adapter = OpenAIAdapter(
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
    decision_model="gpt-4o-2024-08-06",  # Para decisiones estructuradas
    response_model="gpt-4o-mini"          # Para respuestas naturales
)
```

### Ejemplo completo con contexto

```python
from src.adapters import get_default_openai_adapter
from src.core.models import ConversationContext

# Inicializar adapter
adapter = get_default_openai_adapter()

# Crear contexto de conversación
context = ConversationContext(session_id="user-123")
context.add_user_message("Busco un Toyota Corolla")

# Obtener decisión del agente
decision = adapter.get_agent_decision(
    user_text="Busco un Toyota Corolla 2023",
    context=context
)

# Humanizar respuesta
humanized = adapter.humanize_response(
    user_text="Busco un Toyota Corolla",
    action="search_cars",
    base_message="Encontré 5 vehículos",
    vehicles=[{"make": "Toyota", "model": "Corolla", "year": 2023, "price": 350000}]
)

# Generar opciones de financiamiento
financing = adapter.generate_financing_response(
    user_text="¿Cuánto pagaría al mes?",
    vehicle_price=350000.0
)

# Consultar información de Kavak
info = adapter.generate_kavak_info_response(
    user_text="¿Dónde están ubicados?",
    kavak_info="Información completa de Kavak...",
    query="ubicaciones"
)
```

### LocalStorageAdapter (Storage)

#### Importación

```python
from src.adapters import LocalStorageAdapter
```

#### Uso básico

```python
# Crear adapter con TTL de 10 minutos
adapter = LocalStorageAdapter(ttl_minutes=10)

# Obtener o crear sesión
context = await adapter.get_or_create("user-123")

# Agregar mensajes
context.add_user_message("Busco un Toyota Corolla")
context.add_assistant_message("Encontré 5 vehículos")

# Guardar contexto
await adapter.save(context)

# Recuperar contexto
context = await adapter.get("user-123")

# Verificar existencia
exists = await adapter.exists("user-123")

# Eliminar sesión
deleted = await adapter.delete("user-123")

# Limpiar todas las sesiones
count = await adapter.clear_all()
```

#### Gestión de vehículos en contexto

```python
from src.core.models import SelectedVehicle

adapter = LocalStorageAdapter(ttl_minutes=10)
context = await adapter.get_or_create("user-123")

# Guardar resultados de búsqueda
vehicles = [
    SelectedVehicle(
        stock_id=1001,
        make="Toyota",
        model="Corolla",
        year=2023,
        price=350000.0,
        km=15000
    ),
    SelectedVehicle(
        stock_id=1002,
        make="Honda",
        model="Civic",
        year=2023,
        price=380000.0,
        km=12000
    ),
]

context.set_search_results(vehicles)

# Seleccionar un vehículo
success = context.select_vehicle_by_stock_id(1001)

# Guardar cambios
await adapter.save(context)
```

#### Limpieza de sesiones expiradas

```python
adapter = LocalStorageAdapter(ttl_minutes=10)

# Limpiar sesiones expiradas manualmente
cleaned = await adapter.cleanup_expired()
print(f"Limpiadas {cleaned} sesiones expiradas")

# Ver número de sesiones activas
print(f"Sesiones activas: {adapter.session_count}")
```

#### Características de LocalStorageAdapter

- **Thread-safe**: Usa Lock para operaciones concurrentes
- **TTL configurable**: Expiración automática de sesiones
- **Limpieza manual**: Método `cleanup_expired()` para liberar memoria
- **Propiedades útiles**: `session_count`, `ttl_minutes`
- **Async**: Todas las operaciones son async para consistencia

**Cuándo usar:**
- ✅ Desarrollo local
- ✅ Testing
- ✅ Prototipado rápido
- ✅ Ambientes de baja escala

**NO recomendado para:**
- ❌ Producción de alta escala
- ❌ Ambientes distribuidos (múltiples instancias Lambda)
- ❌ Cuando se requiere persistencia entre reinicios

**Para producción, considera:** DynamoDB, Redis, o Elasticache

## 🔄 Migraciones

### Migración desde `llm.client` (OpenAI)

#### Antes (acceso directo)

```python
from src.llm.client import (
    get_agent_decision,
    humanize_response,
    generate_financing_response,
    generate_kavak_info_response
)

decision = get_agent_decision("Busco un auto", context)
```

#### Después (con adapter)

```python
from src.adapters import get_default_openai_adapter

adapter = get_default_openai_adapter()
decision = adapter.get_agent_decision("Busco un auto", context)
```

### Migración desde `agent.context` (Storage)

#### Antes (acceso directo)

```python
from src.agent.context import LocalContextStore

store = LocalContextStore(ttl_minutes=10)
context = await store.get_or_create("user-123")
context.add_user_message("Hola")
await store.save(context)
```

#### Después (con adapter)

```python
from src.adapters import LocalStorageAdapter

adapter = LocalStorageAdapter(ttl_minutes=10)
context = await adapter.get_or_create("user-123")
context.add_user_message("Hola")
await adapter.save(context)
```

**Nota:** `LocalStorageAdapter` es un drop-in replacement de `LocalContextStore`. 
La API es 100% compatible, solo cambia el import y el nombre de la clase.

## ✅ Ventajas del Patrón Adapter

1. **Desacoplamiento**: El código de negocio no depende directamente de OpenAI
2. **Testabilidad**: Fácil crear mocks del adapter para testing
3. **Intercambiabilidad**: Cambiar de proveedor (OpenAI → Anthropic → local model) sin tocar la lógica
4. **Configurabilidad**: Diferentes configuraciones por ambiente (dev, prod)
5. **Dependency Injection**: Inyectar el adapter en servicios

## 🧪 Testing con el Adapter

```python
from unittest.mock import Mock
from src.core.interfaces import LLMAdapter
from src.core.models import AgentAction, AgentDecision

def test_process_message():
    # Crear un mock del adapter
    mock_adapter = Mock(spec=LLMAdapter)
    mock_adapter.get_agent_decision.return_value = AgentDecision(
        action=AgentAction.SEARCH_CARS,
        make="Toyota",
        model="Corolla"
    )
    
    # Inyectar en tu servicio
    service = MyService(llm_adapter=mock_adapter)
    result = service.process("Busco un Toyota")
    
    # Verificar llamadas
    mock_adapter.get_agent_decision.assert_called_once()
```

## 🔮 Futuros Adapters

### LLM Adapters

#### AnthropicAdapter (Claude)

```python
class AnthropicAdapter(LLMAdapter):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def get_agent_decision(self, user_text: str, context=None) -> AgentDecision:
        # Implementación específica de Claude
        pass
```

#### LocalLLMAdapter (Llama, Mistral)

```python
class LocalLLMAdapter(LLMAdapter):
    def __init__(self, model_path: str):
        self.model = load_local_model(model_path)
    
    def get_agent_decision(self, user_text: str, context=None) -> AgentDecision:
        # Implementación para modelos locales
        pass
```

### Storage Adapters

#### DynamoDBStorageAdapter

```python
class DynamoDBStorageAdapter(StorageAdapter):
    """Adapter para almacenamiento en DynamoDB.
    
    Ideal para producción en AWS Lambda:
    - Serverless y escalable
    - Baja latencia
    - TTL nativo de DynamoDB
    - Integración con IAM
    """
    
    def __init__(
        self,
        table_name: str,
        region: str = "us-east-1",
        ttl_minutes: int = 30
    ):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.ttl_minutes = ttl_minutes
    
    async def get(self, session_id: str) -> ConversationContext | None:
        response = self.table.get_item(Key={'session_id': session_id})
        if 'Item' not in response:
            return None
        return self._deserialize(response['Item'])
    
    async def save(self, context: ConversationContext) -> None:
        item = self._serialize(context)
        item['ttl'] = int((datetime.now() + timedelta(minutes=self.ttl_minutes)).timestamp())
        self.table.put_item(Item=item)
```

**Configuración de tabla DynamoDB:**

```yaml
# template.yaml (SAM/CloudFormation)
ConversationTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: kavak-agent-conversations
    AttributeDefinitions:
      - AttributeName: session_id
        AttributeType: S
    KeySchema:
      - AttributeName: session_id
        KeyType: HASH
    BillingMode: PAY_PER_REQUEST
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
```

#### RedisStorageAdapter

```python
class RedisStorageAdapter(StorageAdapter):
    """Adapter para almacenamiento en Redis/Elasticache.
    
    Ideal para:
    - Alta velocidad de lectura/escritura
    - Cache distribuido
    - Sesiones con TTL automático
    - Pub/Sub para eventos
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        ttl_seconds: int = 600,
        db: int = 0
    ):
        self.redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True
        )
        self.ttl_seconds = ttl_seconds
    
    async def get(self, session_id: str) -> ConversationContext | None:
        data = self.redis.get(f"session:{session_id}")
        if not data:
            return None
        return self._deserialize(json.loads(data))
    
    async def save(self, context: ConversationContext) -> None:
        key = f"session:{context.session_id}"
        data = json.dumps(self._serialize(context))
        self.redis.setex(key, self.ttl_seconds, data)
    
    async def clear_all(self) -> int:
        keys = self.redis.keys("session:*")
        if keys:
            return self.redis.delete(*keys)
        return 0
```

**Uso con Redis:**

```python
from src.adapters.storage import RedisStorageAdapter

# Desarrollo local
adapter = RedisStorageAdapter(
    host="localhost",
    port=6379,
    ttl_seconds=600
)

# Producción con Elasticache
adapter = RedisStorageAdapter(
    host="your-elasticache-endpoint.cache.amazonaws.com",
    port=6379,
    password=os.getenv("REDIS_PASSWORD"),
    ttl_seconds=1800  # 30 minutos
)
```

### Comparación de Storage Adapters

| Característica | Local | DynamoDB | Redis |
|---------------|-------|----------|-------|
| **Persistencia** | ❌ En memoria | ✅ Persistente | ⚠️ Persistente con backup |
| **Escalabilidad** | ❌ Single instance | ✅ Serverless | ✅ Cluster |
| **Latencia** | ⚡ Sub-ms | 🚀 1-5 ms | ⚡ Sub-ms |
| **TTL nativo** | ✅ Manual | ✅ Automático | ✅ Automático |
| **Costo** | 💰 Gratis | 💰💰 Por request | 💰💰💰 Por hora |
| **Complejidad** | Simple | Media | Media |
| **AWS Lambda** | ⚠️ No distribuido | ✅ Ideal | ✅ Con VPC |
| **Uso recomendado** | Dev/Test | Producción AWS | High-perf cache |

## 📝 Notas de Implementación

### Caché del Cliente

El adapter usa `@lru_cache` para cachear la instancia por defecto:

```python
@lru_cache(maxsize=1)
def get_default_openai_adapter() -> OpenAIAdapter:
    return OpenAIAdapter()
```

Esto garantiza que solo se cree una instancia del cliente OpenAI durante la ejecución.

### Modelos Configurables

El adapter usa dos modelos:
- **decision_model** (`gpt-4o-2024-08-06`): Para structured outputs (decisiones)
- **response_model** (`gpt-4o-mini`): Para respuestas naturales (más rápido y económico)

### Construcción de Contexto

El adapter incluye métodos privados para formatear el contexto:
- `_build_messages_with_context()`: Construye array de mensajes para OpenAI
- `_format_context_info()`: Formatea información de contexto (búsquedas previas, vehículo seleccionado)

## 🎓 Recursos

- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)

## 🤝 Contribuir

Para agregar un nuevo adapter:

1. Crear nueva clase que herede de `LLMAdapter` o `MessagingAdapter`
2. Implementar todos los métodos abstractos
3. Agregar tests unitarios
4. Actualizar exports en `__init__.py`
5. Documentar el uso en este README

