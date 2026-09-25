#include "ViewerGameMode.h"
#include "ViewerHUD.h"
#include "ViewerPawn.h"
#include "ViewerPlayerController.h"

AViewerGameMode::AViewerGameMode()
{
    DefaultPawnClass = AViewerPawn::StaticClass();
    PlayerControllerClass = AViewerPlayerController::StaticClass();
    HUDClass = AViewerHUD::StaticClass();
}
