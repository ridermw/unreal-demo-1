#include "ViewerPawn.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/FloatingPawnMovement.h"

AViewerPawn::AViewerPawn()
{
    bAddDefaultMovementBindings = false;
    GetMeshComponent()->SetHiddenInGame(true);
    GetMeshComponent()->SetCastShadow(false);
    GetCollisionComponent()->SetSphereRadius(20.f);
    if (UFloatingPawnMovement* Movement = Cast<UFloatingPawnMovement>(GetMovementComponent()))
    {
        Movement->MaxSpeed = 400.f;
        Movement->Acceleration = 1800.f;
        Movement->Deceleration = 3000.f;
        Movement->TurningBoost = 6.f;
    }
}
