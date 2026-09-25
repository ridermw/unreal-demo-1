#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "ViewerHUD.generated.h"

UCLASS()
class PLATFORMNINE_API AViewerHUD : public AHUD
{
    GENERATED_BODY()

public:
    virtual void DrawHUD() override;
    virtual void NotifyHitBoxClick(FName BoxName) override;
};
