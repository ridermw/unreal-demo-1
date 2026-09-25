#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "ViewerPlayerController.generated.h"

class ACameraActor;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

DECLARE_LOG_CATEGORY_EXTERN(LogPlatformViewer, Log, All);

struct FViewerView
{
    FString Label;
    FVector Location;
    FRotator Rotation;
    float FieldOfView = 70.f;
};

UCLASS()
class PLATFORMNINE_API AViewerPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    AViewerPlayerController();
    virtual void Tick(float DeltaSeconds) override;

    void ToggleExplore();
    void ShowMenu();
    void NextView();
    void ToggleFullscreen();
    void ToggleControls();
    void QuitViewer();
    void SelectView(int32 Index);

    bool IsExploring() const { return bExploring; }
    bool AreControlsVisible() const { return bControlsVisible; }
    bool IsViewerReady() const { return bReady; }
    FString GetViewLabel() const;
    const FString& GetViewerError() const { return ViewerError; }
    float GetRenderPercentage() const { return RenderPercentage; }

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void SetupInputComponent() override;

private:
    void CreateInputActions();
    void InitializeViewer();
    void FailInitialization(const FString& Error);
    void SetNavigation(bool bEnabled);
    void Move(const FInputActionValue& Value);
    void Look(const FInputActionValue& Value);
    void StartSprint();
    void StopSprint();
    void ViewOne() { SelectView(0); }
    void ViewTwo() { SelectView(1); }
    void ViewThree() { SelectView(2); }
    void ViewFour() { SelectView(3); }
    void ViewFive() { SelectView(4); }
    void UpdateRenderScale();
    void TickSmokeTest(float DeltaSeconds);
    void FinishSmokeTest(bool bSuccess, const FString& Error = FString());
    void SimulateKey(const FKey& Key, EInputEvent Event, float Amount);

    UPROPERTY()
    TObjectPtr<UInputMappingContext> MappingContext;
    UPROPERTY()
    TObjectPtr<UInputAction> MoveAction;
    UPROPERTY()
    TObjectPtr<UInputAction> LookAction;
    UPROPERTY()
    TArray<TObjectPtr<UInputAction>> ButtonActions;
    UPROPERTY()
    TObjectPtr<ACameraActor> ViewerCamera;

    TArray<FViewerView> Views;
    int32 ActiveView = 0;
    bool bReady = false;
    bool bExploring = false;
    bool bSprinting = false;
    bool bControlsVisible = true;
    FString ViewerError;
    FIntPoint LastViewportSize = FIntPoint::ZeroValue;
    float RenderPercentage = 100.f;
    float ResizeCheckTime = 0.f;
    bool bSmokeTest = false;
    int32 SmokeStage = 0;
    float SmokeStageTime = 0.f;
    float SmokeTotalTime = 0.f;
    FString SmokeDirectory;
    FVector SmokeStartPosition = FVector::ZeroVector;
    FRotator SmokeStartRotation = FRotator::ZeroRotator;
    float SmokeDistance = 0.f;
};
