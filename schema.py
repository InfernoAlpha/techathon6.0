from pydantic import BaseModel,EmailStr,Field
from typing import Literal,Union,Optional,Dict,TypedDict,List,Annotated
from langgraph.graph.message import add_messages
from datetime import date
from langchain_core.messages import BaseMessage

class automotive_state(TypedDict):
    vehicle_id: str
    vehicle_model:str
    customer_name: str
    
    data:Dict
    feedback_url:str

    Data_agent:dict
    Diagnosis_agent:dict
    tts_prompt:str
    feedback_prompt:str
    RCA_CAPA_prompt:str
    conv_result:str
    realtime_telematics: dict
    analysis_result: str
    predicted_failure: Optional[str]
    failure_priority: Optional[str]
    customer_contact_log: List[str]
    customer_response: Optional[str]

    messages: Annotated[list[BaseMessage],add_messages]

class VoiceAppState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    audio_output_path: str

class data_base_schema(BaseModel):
    name:str = Field(...,description="name of the user")
    email:EmailStr = Field(...,description="email of the user")
    model:str = Field(...,description="model of the user vehicle")
    problem:str = Field(...,description="what problem occured in the user's vehicle in brief")
    Date:date = Field(...,description="date of the problem or anamoly occured")

class data_log_feedback(BaseModel):
    name:str = Field(...,description="name of the user")
    model:str = Field(...,description="model of the user vehicle")
    rating:Annotated[float,Field(...,ge=1,le=5,description="can range bertween 1 to 5 inclding 1 and 5 and can have maximum of 2 decimal numbers after the decimal point")]
    feedback:str = Field(...,description="feedback given by the customer")
    Date:date = Field(...,description="date of the feedback")
    garage:Literal["A motors","B motors","c motors"] = Field(...,description="name of the garage customer chose")

class data_fetch_schema(BaseModel):
    vehicle_model: Optional[str] = Field(...,description="the model of the vehicle")

class data_fetch_service_schema(BaseModel):
    key: Literal["name","price","location","slot"] = Field(...,description="specifys which data points to be retrived based on the key given")
    key_value:str = Field(...,description="if the key is name then the key_value would be A motors or B motors etc it would the name of the mechanic garage, if key is slot then key_value would be 2025-11-10 or 2025-11-25")

class data_fetch_slots(BaseModel):
    key: Literal["customer_name","garage_name","price","location","slot"] = Field(...,description="specifys which data points to be retrived based on the key given")
    key_value:str = Field(...,description="if the key is garage_name then the key_value would be A motors or B motors etc it would be the name of the mechanic garage, if key is slot then key_value would be 2025-11-10 or 2025-11-25")

class data_fetch_feedback(BaseModel):
    key: Literal["name","model","rating","feedback","date","garage"] = Field(...,description="specifys which data points to be retrived based on the key given")
    key_value:str = Field(...,description="if the key is garage_name then the key_value would be A motors or B motors etc it would be the name of the mechanic garage, if key is slot then key_value would be 2025-11-10 or 2025-11-25")

class data_log_slots(BaseModel):
    customer_name:str = Field(...,description="the name of the customer")
    garage_name:Literal["A motors","B motors","c motors"] = Field(...,description="name of the garage customer chose")
    price:int = Field(...,description="price of the service")
    location:str = Field(...,description="location of the garage")
    slot:date = Field(...,description="the slot booked for the garage")

class model_schema(BaseModel):
    Engine_rpm : int = Field(...,alias="Engine rpm",description="the rotations per minute of the engine")
    lub_oil_pressure : float = Field(...,alias="Lub oil pressure",description="the pressure of the lubticant oil in the engine")
    Fuel_pressure : float = Field(...,alias = "Fuel pressure",description="the pressure of the fuel in the engine")
    Coolant_pressure : float = Field(...,alias="Coolant pressure",description="the pressure of the coolent in the engine")
    lub_oil_temp : float = Field(...,alias="lub oil temp",description="the temparature of the lubricant oil in the engine")
    Coolant_temp : float = Field(...,alias="Coolant temp",description="the temparature of the coolent in the engine")

class data_output_schema(BaseModel):
    vehicle_id:str = Field(...,description="the unique id of the vehicle")
    status: Literal["ANOMALY_DETECTED","NO_ANOMALY_DETECTED"] = Field(...,description="whether there is any Anomaly detected")
    details:Union[Literal["NONE"],str] = Field(...,description="if there is a ANOMALY specify the anamoly if no ANOMALY detected then just return NONE")
    service_demand:str = Field(...,description="the service needed from the company to fix the anomaly")

class diagnosis_output_schema(BaseModel):
    Probable_component_failure:str = Field(...,description="the predicted component failure in a vehicle, if there are no failures then return NONE")
    priority_level:Literal["NONE","Low","Medium","High"] = Field(...,description="the priority level assigned based on the severity and urgency of the component_failure.If there are no component failures then return NONE")

class doc_gen_format(BaseModel):
    text:str = Field(...,description="the finalized content of RCA/CAPA report")