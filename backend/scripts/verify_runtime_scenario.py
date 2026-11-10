from fastapi.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    payload = {
        'scenario_type': 'moderate_shortage',
        'n_farmers': 6,
        'seed': 42
    }
    response = client.post('/api/v1/scenarios/run', json=payload)
    assert response.status_code == 200, f'Status {response.status_code}: {response.text}'
    data = response.json()
    print('SUCCESS: Scenario executed via API!')
    print(f'Scenario ID: {data["scenario_id"]}')
    print(f'Scenario Type: {data["scenario_type"]}')
    print(f'Available Water: {data["available_water_m3"]} m3')
    print(f'Total Demand (XGBoost): {data["total_demand_m3"]} m3')
    print(f'Allocated Water (OR-Tools): {data["initial_allocation"]["total_allocated_m3"]} m3')
    print(f'Participating Farmers: {data["n_farmers"]}')
    print(f'Allocation Count: {len(data["initial_allocation"]["allocations"])}')
    for alloc in data["initial_allocation"]["allocations"]:
        print(f'  {alloc["farmer_id"]} ({alloc["crop"]}): requested={alloc["predicted_demand_m3"]} m3, allocated={alloc["allocated_water_m3"]} m3, status={alloc["constraint_status"]}')

if __name__ == '__main__':
    main()
