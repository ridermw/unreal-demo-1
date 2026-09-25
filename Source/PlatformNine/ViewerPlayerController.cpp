#include "ViewerPlayerController.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "EngineUtils.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealClient.h"

DEFINE_LOG_CATEGORY(LogPlatformViewer);

AViewerPlayerController::AViewerPlayerController()
{
    bAutoManageActiveCameraTarget = false;
    bEnableClickEvents = true;
    bEnableMouseOverEvents = true;
    PrimaryActorTick.bCanEverTick = true;
}

void AViewerPlayerController::CreateInputActions()
{
    if (MappingContext)
    {
        return;
    }
    MappingContext = NewObject<UInputMappingContext>(this, TEXT("ViewerMapping"));
    auto Action = [this](const TCHAR* Name, EInputActionValueType Type)
    {
        UInputAction* Result = NewObject<UInputAction>(this, FName(Name));
        Result->ValueType = Type;
        return Result;
    };
    auto MapAxis = [this](UInputAction* Input, FKey Key, bool bNegate, int32 Axis)
    {
        FEnhancedActionKeyMapping& Mapping = MappingContext->MapKey(Input, Key);
        if (bNegate)
        {
            Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
        }
        if (Axis != 0)
        {
            UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(MappingContext);
            Swizzle->Order = Axis == 1 ? EInputAxisSwizzle::YXZ : EInputAxisSwizzle::ZYX;
            Mapping.Modifiers.Add(Swizzle);
        }
    };
    MoveAction = Action(TEXT("ViewerMove"), EInputActionValueType::Axis3D);
    MapAxis(MoveAction, EKeys::W, false, 0);
    MapAxis(MoveAction, EKeys::S, true, 0);
    MapAxis(MoveAction, EKeys::D, false, 1);
    MapAxis(MoveAction, EKeys::A, true, 1);
    MapAxis(MoveAction, EKeys::E, false, 2);
    MapAxis(MoveAction, EKeys::Q, true, 2);
    MapAxis(MoveAction, EKeys::SpaceBar, false, 2);
    MapAxis(MoveAction, EKeys::LeftControl, true, 2);
    LookAction = Action(TEXT("ViewerLook"), EInputActionValueType::Axis2D);
    MapAxis(LookAction, EKeys::MouseX, false, 0);
    MapAxis(LookAction, EKeys::MouseY, false, 1);

    const TArray<FKey> Keys = {EKeys::Tab, EKeys::Escape, EKeys::H, EKeys::F11,
                              EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four,
                              EKeys::Five, EKeys::LeftShift};
    for (int32 Index = 0; Index < Keys.Num(); ++Index)
    {
        UInputAction* Button = Action(*FString::Printf(TEXT("ViewerButton%d"), Index),
                                      EInputActionValueType::Boolean);
        ButtonActions.Add(Button);
        MappingContext->MapKey(Button, Keys[Index]);
    }
}

void AViewerPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    CreateInputActions();
    UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent);
    if (!ensureMsgf(Input, TEXT("Viewer requires EnhancedInputComponent")))
    {
        ViewerError = TEXT("Input initialization failed.");
        UE_LOG(LogPlatformViewer, Error, TEXT("%s"), *ViewerError);
        return;
    }
    Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &ThisClass::Move);
    Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &ThisClass::Look);
    Input->BindAction(ButtonActions[0], ETriggerEvent::Started, this, &ThisClass::ToggleExplore);
    Input->BindAction(ButtonActions[1], ETriggerEvent::Started, this, &ThisClass::ShowMenu);
    Input->BindAction(ButtonActions[2], ETriggerEvent::Started, this, &ThisClass::ToggleControls);
    Input->BindAction(ButtonActions[3], ETriggerEvent::Started, this, &ThisClass::ToggleFullscreen);
    Input->BindAction(ButtonActions[4], ETriggerEvent::Started, this, &ThisClass::ViewOne);
    Input->BindAction(ButtonActions[5], ETriggerEvent::Started, this, &ThisClass::ViewTwo);
    Input->BindAction(ButtonActions[6], ETriggerEvent::Started, this, &ThisClass::ViewThree);
    Input->BindAction(ButtonActions[7], ETriggerEvent::Started, this, &ThisClass::ViewFour);
    Input->BindAction(ButtonActions[8], ETriggerEvent::Started, this, &ThisClass::ViewFive);
    Input->BindAction(ButtonActions[9], ETriggerEvent::Started, this, &ThisClass::StartSprint);
    Input->BindAction(ButtonActions[9], ETriggerEvent::Completed, this, &ThisClass::StopSprint);
    Input->BindAction(ButtonActions[9], ETriggerEvent::Canceled, this, &ThisClass::StopSprint);
}

void AViewerPlayerController::BeginPlay()
{
    Super::BeginPlay();
    if (IsLocalController())
    {
        bSmokeTest = FParse::Param(FCommandLine::Get(), TEXT("ViewerSmokeTest"));
        if (bSmokeTest)
        {
            FParse::Value(FCommandLine::Get(), TEXT("ViewerEvidenceDir="), SmokeDirectory);
            TArray<FString> Existing;
            if (!SmokeDirectory.IsEmpty())
            {
                IFileManager::Get().FindFilesRecursive(Existing, *SmokeDirectory, TEXT("*"), true, true);
            }
            if (SmokeDirectory.IsEmpty() || FPaths::IsRelative(SmokeDirectory) || !Existing.IsEmpty())
            {
                SmokeDirectory.Reset();
                FailInitialization(TEXT("Smoke evidence must use a fresh, empty, absolute directory."));
                return;
            }
            if (!IFileManager::Get().MakeDirectory(*SmokeDirectory, true))
            {
                SmokeDirectory.Reset();
                FailInitialization(TEXT("Cannot create smoke evidence directory."));
                return;
            }
        }
        GetWorldTimerManager().SetTimerForNextTick(this, &ThisClass::InitializeViewer);
    }
}

void AViewerPlayerController::FailInitialization(const FString& Error)
{
    ViewerError = Error;
    UE_LOG(LogPlatformViewer, Error, TEXT("%s"), *ViewerError);
    if (bSmokeTest)
    {
        FinishSmokeTest(false, ViewerError);
    }
}

void AViewerPlayerController::InitializeViewer()
{
    CreateInputActions();
    ULocalPlayer* Local = GetLocalPlayer();
    UEnhancedInputLocalPlayerSubsystem* Input = Local ? Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
    if (!Input || !GetPawn() || !ViewerError.IsEmpty())
    {
        FailInitialization(TEXT("The walkthrough could not initialize its player/input."));
        return;
    }
    Input->AddMappingContext(MappingContext, 0);
    ACameraActor* Reference = nullptr;
    for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
    {
        if (It->GetAutoActivatePlayerIndex() == 0)
        {
            if (Reference)
            {
                FailInitialization(TEXT("Multiple presentation cameras found."));
                return;
            }
            Reference = *It;
        }
    }
    if (!Reference)
    {
        FailInitialization(TEXT("The saved platform presentation camera is missing."));
        return;
    }
    Views.Add({TEXT("Main platform"), Reference->GetActorLocation(), Reference->GetActorRotation(),
               Reference->GetCameraComponent()->FieldOfView});
    auto AddView = [this](const TCHAR* Label, FVector Location, FVector Target, float Fov)
    {
        Views.Add({Label, Location, (Target - Location).Rotation(), Fov});
    };
    AddView(TEXT("Locomotive"), FVector(25, -580, 195), FVector(-230, -530, 135), 60);
    AddView(TEXT("Luggage"), FVector(270, 340, 220), FVector(400, 120, 155), 55);
    AddView(TEXT("Opposite platform"), FVector(-590, -500, 235), FVector(-970, -1100, 400), 65);
    AddView(TEXT("Down the platform"), FVector(170, -2500, 235), FVector(150, 0, 220), 70);
    FActorSpawnParameters Spawn;
    Spawn.ObjectFlags |= RF_Transient;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ViewerCamera = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), FTransform::Identity, Spawn);
    if (!ViewerCamera)
    {
        FailInitialization(TEXT("Cannot create the walkthrough camera."));
        return;
    }
    ViewerCamera->GetCameraComponent()->bConstrainAspectRatio = true;
    ViewerCamera->GetCameraComponent()->AspectRatio = 16.f / 9.f;
    ViewerCamera->GetCameraComponent()->PostProcessBlendWeight = 0.f;
    PlayerCameraManager->ViewPitchMin = -85.f;
    PlayerCameraManager->ViewPitchMax = 85.f;
    if (UGameUserSettings* Settings = GEngine->GetGameUserSettings())
    {
        Settings->SetOverallScalabilityLevel(2);
        Settings->SetVSyncEnabled(false);
        Settings->SetFrameRateLimit(32.f);
        if (!FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen")))
        {
            Settings->SetScreenResolution(FIntPoint(1536, 864));
            Settings->SetFullscreenMode(EWindowMode::Windowed);
        }
        Settings->ApplySettings(false);
    }
    bReady = true;
    SelectView(0);
    UpdateRenderScale();
    UE_LOG(LogPlatformViewer, Display, TEXT("VIEWER_READY map=%s views=%d"), *GetWorld()->GetMapName(), Views.Num());
}

void AViewerPlayerController::EndPlay(const EEndPlayReason::Type Reason)
{
    if (ULocalPlayer* Local = GetLocalPlayer())
    {
        if (UEnhancedInputLocalPlayerSubsystem* Input = Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            Input->RemoveMappingContext(MappingContext);
        }
    }
    Super::EndPlay(Reason);
}

void AViewerPlayerController::SetNavigation(bool bEnabled)
{
    bExploring = bEnabled;
    bShowMouseCursor = !bEnabled;
    if (bEnabled)
    {
        SetInputMode(FInputModeGameOnly().SetConsumeCaptureMouseDown(false));
    }
    else
    {
        bSprinting = false;
        if (GetPawn() && GetPawn()->GetMovementComponent())
        {
            GetPawn()->GetMovementComponent()->StopMovementImmediately();
        }
        FInputModeGameAndUI Mode;
        Mode.SetHideCursorDuringCapture(false);
        Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        SetInputMode(Mode);
    }
}

void AViewerPlayerController::ToggleExplore()
{
    if (!bReady)
    {
        return;
    }
    if (bExploring)
    {
        ShowMenu();
        return;
    }
    FVector Location;
    FRotator Rotation;
    GetPlayerViewPoint(Location, Rotation);
    GetPawn()->SetActorLocationAndRotation(Location, Rotation, false, nullptr, ETeleportType::TeleportPhysics);
    SetControlRotation(Rotation);
    SetViewTarget(GetPawn());
    PlayerCameraManager->SetFOV(70.f);
    SetNavigation(true);
}

void AViewerPlayerController::ShowMenu()
{
    bControlsVisible = true;
    SetNavigation(false);
}

void AViewerPlayerController::SelectView(int32 Index)
{
    if (!bReady || !Views.IsValidIndex(Index))
    {
        return;
    }
    ActiveView = Index;
    const FViewerView& View = Views[Index];
    SetNavigation(false);
    ViewerCamera->SetActorLocationAndRotation(View.Location, View.Rotation);
    ViewerCamera->GetCameraComponent()->SetFieldOfView(View.FieldOfView);
    PlayerCameraManager->UnlockFOV();
    SetViewTarget(ViewerCamera);
    UE_LOG(LogPlatformViewer, Display, TEXT("VIEWER_PRESET %d %s"), Index + 1, *View.Label);
}

void AViewerPlayerController::NextView() { SelectView((ActiveView + 1) % FMath::Max(Views.Num(), 1)); }
void AViewerPlayerController::ToggleControls() { bControlsVisible = !bControlsVisible; }
void AViewerPlayerController::StartSprint() { bSprinting = true; }
void AViewerPlayerController::StopSprint() { bSprinting = false; }

void AViewerPlayerController::Move(const FInputActionValue& Value)
{
    if (!bExploring || !GetPawn())
    {
        return;
    }
    const FVector Axis = Value.Get<FVector>().GetClampedToMaxSize(1.f);
    const FRotator Rotation = GetControlRotation();
    GetPawn()->AddMovementInput(Rotation.Vector(), Axis.X);
    GetPawn()->AddMovementInput(FRotationMatrix(Rotation).GetUnitAxis(EAxis::Y), Axis.Y);
    GetPawn()->AddMovementInput(FVector::UpVector, Axis.Z);
}

void AViewerPlayerController::Look(const FInputActionValue& Value)
{
    if (bExploring)
    {
        const FVector2D Axis = Value.Get<FVector2D>();
        AddYawInput(Axis.X * .15f);
        AddPitchInput(Axis.Y * .15f);
    }
}

FString AViewerPlayerController::GetViewLabel() const
{
    if (bExploring) { return TEXT("Free exploration"); }
    if (bReady && GetViewTarget() == GetPawn()) { return TEXT("Exploration paused"); }
    return Views.IsValidIndex(ActiveView) ? Views[ActiveView].Label : TEXT("Loading");
}

void AViewerPlayerController::ToggleFullscreen()
{
    if (UGameUserSettings* Settings = GEngine->GetGameUserSettings())
    {
        const bool bWindowed = Settings->GetFullscreenMode() == EWindowMode::Windowed;
        Settings->SetFullscreenMode(bWindowed ? EWindowMode::WindowedFullscreen : EWindowMode::Windowed);
        if (!bWindowed)
        {
            Settings->SetScreenResolution(FIntPoint(1536, 864));
        }
        Settings->ApplyResolutionSettings(false);
        LastViewportSize = FIntPoint::ZeroValue;
    }
}

void AViewerPlayerController::QuitViewer()
{
    UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

void AViewerPlayerController::UpdateRenderScale()
{
    if (!GEngine || !GEngine->GameViewport || !GEngine->GameViewport->Viewport)
    {
        return;
    }
    const FIntPoint Size = GEngine->GameViewport->Viewport->GetSizeXY();
    if (Size.X <= 0 || Size.Y <= 0 || Size == LastViewportSize)
    {
        return;
    }
    LastViewportSize = Size;
    RenderPercentage = FMath::Clamp(FMath::Min(1536.f / Size.X, 864.f / Size.Y) * 100.f, 25.f, 100.f);
    if (IConsoleVariable* Percentage = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))
    {
        Percentage->Set(RenderPercentage, ECVF_SetByCode);
    }
    UE_LOG(LogPlatformViewer, Display, TEXT("VIEWER_RESOLUTION %dx%d screen_percentage=%.2f"),
           Size.X, Size.Y, RenderPercentage);
}

void AViewerPlayerController::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (UFloatingPawnMovement* Movement = GetPawn() ? Cast<UFloatingPawnMovement>(GetPawn()->GetMovementComponent()) : nullptr)
    {
        Movement->MaxSpeed = bSprinting ? 1000.f : 400.f;
    }
    ResizeCheckTime += DeltaSeconds;
    if (ResizeCheckTime >= .5f)
    {
        ResizeCheckTime = 0.f;
        UpdateRenderScale();
    }
    if (bSmokeTest)
    {
        TickSmokeTest(DeltaSeconds);
    }
}
