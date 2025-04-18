# buy-available-pet

This workflow demonstrates a workflow very similar to `apply-coupon`, by intention. It's meant to indicate how to reuse a step (`place-order`) as well as a parameter (`page`, `pageSize`).

## Workflow Diagram

```plantuml
@startuml
skinparam backgroundColor #EEEBDC
skinparam handwritten true

participant "buy-available-pet" as buy_available_pet
participant "find-pet" as find_pet
participant "place-order" as place_order
buy_available_pet --> find_pet : None
buy_available_pet --> place_order : None
@enduml
```

## Steps

### find-pet

**ID**: find-pet

None

### place-order

**ID**: place-order

None

